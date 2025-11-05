<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import axios from 'axios';
import { BOOK_SERVICE_URL } from '../../config';
import { useAuth } from '../../composables/useAuth'; 
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue';
import { ChevronDownIcon } from '@heroicons/vue/20/solid';

const props = defineProps<{
  bookId: number;
  initialStatus: string; 
}>();

const { userInfo } = useAuth();
const loading = ref(false);
const status = ref(props.initialStatus || 'to_read'); 

const statusMap = {
  to_read: "Muốn đọc",
  currently_reading: "Đang đọc",
  read: "Đã đọc",
  dnf: "Bỏ dở",
};

watch(() => props.initialStatus, (newVal) => {
  status.value = newVal || 'to_read';
});

async function updateStatus(newStatus: 'to_read' | 'currently_reading' | 'read' | 'dnf') {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!userId) {
    alert("Vui lòng đăng nhập");
    return;
  }
  
  loading.value = true;
  try {
    await axios.put(
      `${BOOK_SERVICE_URL}books/${props.bookId}/status?user_id=${userId}&status=${newStatus}`
    );
    status.value = newStatus;
  } catch (err: any) {
    alert(err.response?.data?.detail || "Lỗi cập nhật");
  } finally {
    loading.value = false;
  }
}

const otherOptions = computed(() => {
  return (Object.keys(statusMap) as (keyof typeof statusMap)[])
    .filter(key => key !== status.value);
});
</script>

<template>
  <Menu as="div" class="relative inline-block text-left w-full">
    <div>
      <MenuButton 
        :disabled="loading"
        class="flex w-full justify-between items-center rounded-md bg-yellow-400 px-3 py-2 text-sm font-semibold text-black shadow-sm hover:bg-yellow-500 disabled:opacity-50"
      >
        <span>{{ statusMap[status as keyof typeof statusMap] }}</span>
        <ChevronDownIcon class="h-5 w-5" aria-hidden="true" />
      </MenuButton>
    </div>

    <transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <MenuItems class="absolute right-0 z-10 mt-2 w-full origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
        <div class="py-1">
          <MenuItem 
            v-for="key in otherOptions" 
            :key="key" 
            v-slot="{ active }"
          >
            <button
              @click="updateStatus(key)"
              :class="[
                active ? 'bg-gray-100 text-gray-900' : 'text-gray-700',
                'block w-full text-left px-4 py-2 text-sm'
              ]"
            >
              {{ statusMap[key] }}
            </button>
          </MenuItem>
        </div>
      </MenuItems>
    </transition>
  </Menu>
</template>

