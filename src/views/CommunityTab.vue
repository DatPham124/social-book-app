<script setup lang="ts">
import { ref } from 'vue'
import Navbar from '../components/layout/Navbar.vue'
import BookClub from '../components/Community/BookClub.vue'

// Danh sách các tab tiếng Việt
const tabs = [
  { name: 'Bản Tin', value: 'newsfeed' },
  { name: 'Đọc Cùng Bạn', value: 'buddyreads' },
  { name: 'Đọc Theo Nhóm', value: 'readalongs' },
  { name: 'Câu Lạc Bộ Sách', value: 'bookclubs' },
  { name: 'Người Dùng Tương Tự', value: 'similarusers' },
]

const activeTab = ref('newsfeed')

function selectTab(tabValue: string) {
  activeTab.value = tabValue
}
</script>

<template>
  <Navbar />

  <div class="w-full max-w-5xl mx-auto mt-10 px-4">
    <!-- Tiêu đề -->
    <h2 class="text-2xl font-logo text-yellow-400 mb-6">Cộng đồng</h2>

    <!-- Tabs -->
    <div class="flex flex-wrap gap-6 border-b border-gray-300">
      <button v-for="tab in tabs" :key="tab.value" @click="selectTab(tab.value)"
        class="relative pb-2 text-gray-600 hover:text-yellow-400 font-medium transition-colors duration-200">
        <span>{{ tab.name }}</span>
        <span v-if="activeTab === tab.value"
          class="absolute left-0 bottom-0 w-full h-[2px] bg-yellow-400 rounded-full "></span>
      </button>
    </div>

    <!-- Nội dung tab -->
    <div class="mt-8">
      <div v-if="activeTab === 'newsfeed'">
        <p class="text-gray-400 text-base">📢 Đây là <b>Bản Tin</b> — nơi cập nhật các hoạt động và chia sẻ từ cộng
          đồng.</p>
      </div>

      <div v-else-if="activeTab === 'buddyreads'">
        <p class="text-gray-400 text-base">📚 Đây là <b>Đọc Cùng Bạn</b> — nơi bạn và bạn bè cùng chọn sách để đọc
          chung.</p>
      </div>

      <div v-else-if="activeTab === 'readalongs'">
        <p class="text-gray-400 text-base">🎧 Đây là <b>Đọc Theo Nhóm</b> — các hoạt động đọc sách tập thể theo chủ đề.
        </p>
      </div>

      <div v-else-if="activeTab === 'bookclubs'">
        <BookClub />
      </div>

      <div v-else-if="activeTab === 'similarusers'">
        <p class="text-gray-400 text-base">👥 Đây là <b>Người Dùng Tương Tự</b> — gợi ý những người có sở thích đọc
          giống bạn.</p>
      </div>
    </div>
  </div>
</template>
