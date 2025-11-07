"""评分数据仓库"""

from typing import List, Dict
from collections import defaultdict
from functools import wraps
from backend.db.hbase import hbase_connection
from backend.core.logging import logger


def retry_on_connection_error(max_retries=2):
    """连接错误时自动重试的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    # 每次重试前刷新表连接
                    if hasattr(self, '_refresh_table'):
                        self._refresh_table()
                    return func(self, *args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()
                    # 判断是否是连接错误
                    if 'connection' in error_msg or 'broken pipe' in error_msg or '10053' in error_msg:
                        logger.warning(f"连接错误，尝试重连 (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            continue
                    # 非连接错误直接抛出
                    raise
            raise last_error
        return wrapper
    return decorator


class RatingRepository:
    """评分数据访问对象"""
    
    def __init__(self):
        self.table = None
        self._refresh_table()
    
    def _refresh_table(self):
        """刷新表连接"""
        self.table = hbase_connection.get_ratings_table()
    
    @retry_on_connection_error(max_retries=2)
    def find_by_movie_id(self, movie_id: str, limit: int = None) -> List[dict]:
        """查找电影的评分记录
        
        Args:
            movie_id: 电影ID
            limit: 返回数量限制，None表示返回全部
            
        Returns:
            List[dict]: 评分记录列表
        """
        ratings = []
        try:
            for key, data in self.table.scan():
                key_str = key.decode('utf-8')
                parts = key_str.split('_')
                
                if len(parts) == 2:
                    user_id, mid = parts
                    if mid == movie_id:
                        ratings.append({
                            'user_id': user_id,
                            'movie_id': mid,
                            'rating': data.get(b'data:rating', b'0').decode('utf-8'),
                            'timestamp': data.get(b'data:timestamp', b'').decode('utf-8')
                        })
                        
                        if limit and len(ratings) >= limit:
                            break
            
            return ratings
        except Exception as e:
            logger.error(f"查询电影评分失败 movie_id={movie_id}: {e}")
            raise
    
    @retry_on_connection_error(max_retries=2)
    def get_rating_stats(self, movie_id: str) -> dict:
        """获取电影评分统计
        
        Args:
            movie_id: 电影ID
            
        Returns:
            dict: 评分统计信息
        """
        try:
            # 获取所有评分
            all_ratings = self.find_by_movie_id(movie_id, limit=None)
            
            if not all_ratings:
                return {
                    'avg_rating': 0.0,
                    'total_count': 0,
                    'rating_distribution': {}
                }
            
            # 计算统计信息
            total = 0.0
            distribution = defaultdict(int)
            
            for r in all_ratings:
                rating_value = float(r['rating'])
                total += rating_value
                # 评分分布（按整数分组，如 0.5-1.0 算作 1，1.5-2.0 算作 2）
                rating_key = str(int(rating_value)) if rating_value >= 1 else "0.5"
                distribution[rating_key] += 1
            
            return {
                'avg_rating': total / len(all_ratings),
                'total_count': len(all_ratings),
                'rating_distribution': dict(distribution)
            }
        except Exception as e:
            logger.error(f"获取评分统计失败 movie_id={movie_id}: {e}")
            raise
    
    @retry_on_connection_error(max_retries=2)
    def find_by_user_id(self, user_id: str, limit: int = 10) -> List[dict]:
        """查找用户的评分记录
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            List[dict]: 评分记录列表
        """
        ratings = []
        try:
            # 使用前缀扫描优化查询
            start_row = f"{user_id}_".encode('utf-8')
            stop_row = f"{user_id}_~".encode('utf-8')
            
            for key, data in self.table.scan(row_start=start_row, row_stop=stop_row):
                key_str = key.decode('utf-8')
                parts = key_str.split('_')
                
                if len(parts) == 2:
                    uid, movie_id = parts
                    ratings.append({
                        'user_id': uid,
                        'movie_id': movie_id,
                        'rating': data.get(b'data:rating', b'0').decode('utf-8'),
                        'timestamp': data.get(b'data:timestamp', b'').decode('utf-8')
                    })
                    
                    if len(ratings) >= limit:
                        break
            
            return ratings
        except Exception as e:
            logger.error(f"查询用户评分失败 user_id={user_id}: {e}")
            raise
