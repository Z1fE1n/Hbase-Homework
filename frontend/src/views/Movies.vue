<template>
  <div class="movies-page">
    <div class="page-container">
      <div class="page-header">
        <h1 class="page-title">电影库</h1>
        <p class="page-subtitle">探索数万部精选电影</p>
      </div>
      
      <div v-if="loading && !movies.length" class="loading-state">
        <div class="spinner"></div>
      </div>
      
      <div v-else>
        <div class="movies-grid">
          <MovieCard
            v-for="movie in movies"
            :key="movie.id"
            :movie="movie"
          />
        </div>
        
        <div v-if="totalPages > 1" class="pagination">
          <button
            class="pagination-btn"
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
          >
            <i class="ri-arrow-left-s-line"></i>
          </button>
          
          <div class="pagination-numbers">
            <button
              v-for="page in visiblePages"
              :key="page"
              class="pagination-number"
              :class="{ active: page === currentPage }"
              @click="goToPage(page)"
            >
              {{ page }}
            </button>
          </div>
          
          <button
            class="pagination-btn"
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
            <i class="ri-arrow-right-s-line"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { movieApi } from '@/services/api'
import MovieCard from '@/components/MovieCard.vue'

const route = useRoute()
const router = useRouter()

const movies = ref([])
const loading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)
const total = ref(0)

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 7
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

const loadMovies = async (page = 1) => {
  try {
    loading.value = true
    const response = await movieApi.getMovies(page, 20)
    movies.value = response.movies
    currentPage.value = response.page
    totalPages.value = response.total_pages
    total.value = response.total
    
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (error) {
    console.error('加载电影列表失败:', error)
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    router.push({ query: { page } })
  }
}

watch(() => route.query.page, (newPage) => {
  const page = parseInt(newPage) || 1
  loadMovies(page)
})

onMounted(() => {
  const page = parseInt(route.query.page) || 1
  loadMovies(page)
})
</script>

<style scoped>
.movies-page {
  min-height: 100vh;
  padding: 40px;
}

.page-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 60px;
}

.page-title {
  font-size: 48px;
  font-weight: 700;
  margin: 0 0 12px 0;
  letter-spacing: -1px;
}

.page-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.movies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 32px;
  margin-bottom: 60px;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 120px 0;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.pagination-btn {
  width: 44px;
  height: 44px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.pagination-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.pagination-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.pagination-numbers {
  display: flex;
  gap: 8px;
}

.pagination-number {
  width: 44px;
  height: 44px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.6);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 15px;
  font-weight: 500;
}

.pagination-number:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.pagination-number.active {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
}

@media (max-width: 768px) {
  .movies-page {
    padding: 20px;
  }
  
  .page-title {
    font-size: 32px;
  }
  
  .movies-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 20px;
  }
  
  .pagination-btn,
  .pagination-number {
    width: 36px;
    height: 36px;
  }
}
</style>

