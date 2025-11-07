"""电影业务逻辑服务"""

from typing import List, Optional, Tuple
from backend.db.repositories.movie_repository import MovieRepository
from backend.db.repositories.rating_repository import RatingRepository
from backend.models.domain import Movie, Rating, MovieDetail
from backend.core.config import settings
from backend.core.logging import logger


class MovieService:
    """电影业务服务"""
    
    def __init__(self):
        self.movie_repo = MovieRepository()
        self.rating_repo = RatingRepository()
    
    def get_movies_list(self, page: int = 1, page_size: int = 20) -> tuple:
        """获取电影列表（分页）
        
        Args:
            page: 页码
            page_size: 每页数量
            
        Returns:
            tuple: (电影列表, 总数, 总页数)
        """
        try:
            # 获取所有电影
            all_movies_data = self.movie_repo.find_all()
            
            # 转换为领域模型
            all_movies = [
                Movie(
                    id=m['id'],
                    title=m['title'],
                    genres=m['genres'],
                    avg_rating=float(m['avg_rating']),
                    rating_count=int(m['rating_count'])
                )
                for m in all_movies_data
            ]
            
            # 按评分排序
            all_movies.sort(key=lambda x: (x.avg_rating, x.rating_count), reverse=True)
            
            # 分页处理
            total = len(all_movies)
            total_pages = (total + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            movies = all_movies[start_idx:end_idx]
            
            return movies, total, total_pages
        except Exception as e:
            logger.error(f"获取电影列表失败: {e}")
            raise
    
    def get_movie_by_id(self, movie_id: str) -> Optional[MovieDetail]:
        """根据ID获取电影详情
        
        Args:
            movie_id: 电影ID
            
        Returns:
            Optional[MovieDetail]: 电影详情，不存在返回None
        """
        try:
            # 获取电影基本信息
            movie_data = self.movie_repo.find_by_id(movie_id)
            if not movie_data:
                return None
            
            # 获取最近评分（前10条）
            ratings_data = self.rating_repo.find_by_movie_id(movie_id, limit=10)
            ratings = [
                Rating(
                    user_id=r['user_id'],
                    movie_id=r['movie_id'],
                    rating=float(r['rating']),
                    timestamp=r['timestamp']
                )
                for r in ratings_data
            ]
            
            # 构建详情对象
            return MovieDetail(
                id=movie_data['id'],
                title=movie_data['title'],
                genres=movie_data['genres'],
                avg_rating=float(movie_data['avg_rating']),
                rating_count=int(movie_data['rating_count']),
                recent_ratings=ratings
            )
        except Exception as e:
            logger.error(f"获取电影详情失败 movie_id={movie_id}: {e}")
            raise
    
    def get_movie_ratings(self, movie_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[Rating], int, int]:
        """获取电影的所有评分（分页）
        
        Args:
            movie_id: 电影ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            tuple: (评分列表, 总数, 总页数)
        """
        try:
            # 获取所有评分
            all_ratings_data = self.rating_repo.find_by_movie_id(movie_id, limit=None)
            
            # 转换为领域模型
            all_ratings = [
                Rating(
                    user_id=r['user_id'],
                    movie_id=r['movie_id'],
                    rating=float(r['rating']),
                    timestamp=r['timestamp']
                )
                for r in all_ratings_data
            ]
            
            # 按时间戳倒序排序（最新的在前）
            all_ratings.sort(key=lambda x: x.timestamp, reverse=True)
            
            # 分页处理
            total = len(all_ratings)
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            ratings = all_ratings[start_idx:end_idx]
            
            return ratings, total, total_pages
        except Exception as e:
            logger.error(f"获取电影评分列表失败 movie_id={movie_id}: {e}")
            raise
    
    def get_rating_stats(self, movie_id: str) -> dict:
        """获取电影评分统计
        
        Args:
            movie_id: 电影ID
            
        Returns:
            dict: 评分统计信息
        """
        try:
            return self.rating_repo.get_rating_stats(movie_id)
        except Exception as e:
            logger.error(f"获取评分统计失败 movie_id={movie_id}: {e}")
            raise
    
    def search_movies(self, query: str, limit: int = 50) -> List[Movie]:
        """搜索电影
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            List[Movie]: 匹配的电影列表
        """
        try:
            query = query.strip()
            if not query:
                return []
            
            # 检查是否为ID查询
            if query.isdigit():
                movie_data = self.movie_repo.find_by_id(query)
                if movie_data:
                    return [
                        Movie(
                            id=movie_data['id'],
                            title=movie_data['title'],
                            genres=movie_data['genres'],
                            avg_rating=float(movie_data['avg_rating']),
                            rating_count=int(movie_data['rating_count'])
                        )
                    ]
                return []
            
            # 文本搜索
            matched_data = self.movie_repo.search_by_text(query, limit)
            matched_movies = [
                Movie(
                    id=m['id'],
                    title=m['title'],
                    genres=m['genres'],
                    avg_rating=float(m['avg_rating']),
                    rating_count=int(m['rating_count'])
                )
                for m in matched_data
            ]
            
            # 按相关度排序（标题匹配优先，然后按评分）
            def sort_key(movie: Movie):
                title_match = query.lower() in movie.title.lower()
                return (not title_match, -movie.avg_rating, -movie.rating_count)
            
            matched_movies.sort(key=sort_key)
            
            return matched_movies
        except Exception as e:
            logger.error(f"搜索电影失败 query={query}: {e}")
            raise
