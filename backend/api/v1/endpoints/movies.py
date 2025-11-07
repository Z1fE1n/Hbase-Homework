"""电影相关端点"""

from fastapi import APIRouter, HTTPException, Query
from backend.services.movie_service import MovieService
from backend.models.schemas import (
    MovieListResponse, MovieDetailSchema, MovieSchema,
    SearchResponse, RatingSchema, RatingListResponse,
    RatingStatsSchema
)
from backend.core.config import settings
from backend.core.logging import logger

router = APIRouter()
movie_service = MovieService()


@router.get("", response_model=MovieListResponse)
async def list_movies(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取电影列表（分页）"""
    try:
        movies, total, total_pages = movie_service.get_movies_list(page, page_size)
        
        return MovieListResponse(
            movies=[MovieSchema.model_validate(m.__dict__) for m in movies],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"获取电影列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取电影列表失败")


@router.get("/search", response_model=SearchResponse)
async def search_movies(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(50, ge=1, le=100, description="返回结果数量")
):
    """搜索电影"""
    try:
        movies = movie_service.search_movies(q, limit)
        
        return SearchResponse(
            movies=[MovieSchema.model_validate(m.__dict__) for m in movies],
            query=q,
            total=len(movies)
        )
    except Exception as e:
        logger.error(f"搜索电影失败: {e}")
        raise HTTPException(status_code=500, detail="搜索失败")


@router.get("/{movie_id}", response_model=MovieDetailSchema)
async def get_movie(movie_id: str):
    """获取电影详情"""
    try:
        movie = movie_service.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="电影不存在")
        
        # 获取评分统计
        rating_stats = movie_service.get_rating_stats(movie_id)
        
        return MovieDetailSchema(
            id=movie.id,
            title=movie.title,
            genres=movie.genres,
            avg_rating=movie.avg_rating,
            rating_count=movie.rating_count,
            recent_ratings=[
                RatingSchema.model_validate(r.__dict__) 
                for r in movie.recent_ratings
            ],
            rating_stats=RatingStatsSchema(**rating_stats)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取电影详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取电影详情失败")


@router.get("/{movie_id}/ratings", response_model=RatingListResponse)
async def get_movie_ratings(
    movie_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取电影的所有评分（分页）"""
    try:
        logger.info(f"获取电影评分列表: movie_id={movie_id}, page={page}, page_size={page_size}")
        
        ratings, total, total_pages = movie_service.get_movie_ratings(
            movie_id, page, page_size
        )
        
        # 转换为schema，确保所有字段都存在
        rating_schemas = []
        for r in ratings:
            rating_schemas.append(RatingSchema(
                user_id=str(r.user_id),
                movie_id=str(r.movie_id),
                rating=float(r.rating),
                timestamp=str(r.timestamp)
            ))
        
        response = RatingListResponse(
            ratings=rating_schemas,
            total=int(total),
            page=int(page),
            page_size=int(page_size),
            total_pages=int(total_pages)
        )
        
        logger.info(f"成功返回 {len(rating_schemas)} 条评分")
        return response
        
    except ValueError as e:
        logger.error(f"参数验证失败: {e}")
        raise HTTPException(status_code=422, detail=f"参数错误: {str(e)}")
    except Exception as e:
        logger.error(f"获取电影评分列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取评分列表失败")
