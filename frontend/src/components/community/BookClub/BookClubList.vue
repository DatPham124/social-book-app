<script setup lang="ts">
import { BOOKCLUB_IMAGE_SERVER_URL } from '../../../config';

const props = defineProps<{
  clubs: any[]
}>();
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <router-link
      v-for="club in props.clubs"
      :key="club.id"
      :to="'/bookclub/' + club.id"
      class="block bg-white p-4 rounded-lg border shadow-sm hover:shadow-md transition"
    >
      <div class="flex items-center gap-4">
        <img 
          v-if="club.avatar_url"
          :src="`${BOOKCLUB_IMAGE_SERVER_URL}/${club.avatar_url}`"
          class="w-16 h-16 object-cover rounded-md flex-shrink-0"
        />
        <div v-else class="w-16 h-16 bg-gray-200 rounded-md flex items-center justify-center font-bold text-2xl text-gray-500 flex-shrink-0">
          {{ club.name.charAt(0).toUpperCase() }}
        </div>
        <div class="overflow-hidden">
          <h3 class="font-semibold text-gray-800 truncate">{{ club.name }}</h3>
          <p class="text-sm text-gray-500 truncate">{{ club.description || 'Chưa có mô tả' }}</p>
        </div>
      </div>
    </router-link>
  </div>
</template>

