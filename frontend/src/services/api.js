import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const movieApi = {
  // 获取电影列表
  getMovies(page = 1, pageSize = 20) {
    return api.get('/movies', { params: { page, page_size: pageSize } })
  },

  // 搜索电影
  searchMovies(query, limit = 50) {
    return api.get('/movies/search', { params: { q: query, limit } })
  },

  // 获取电影详情
  getMovieDetail(id) {
    return api.get(`/movies/${id}`)
  },

  // 获取电影评分列表
  getMovieRatings(id, page = 1, pageSize = 20) {
    return api.get(`/movies/${id}/ratings`, { params: { page, page_size: pageSize } })
  }
}

export default api



