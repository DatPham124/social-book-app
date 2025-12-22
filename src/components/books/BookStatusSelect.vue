<script setup lang="ts">
import { computed } from 'vue'; 
import axios from "axios";
import { BOOK_SERVICE_URL } from "../../config.ts";
import { Listbox, ListboxButton, ListboxOption, ListboxOptions } from "@headlessui/vue";
import { ChevronUpDownIcon } from "@heroicons/vue/20/solid";

const props = defineProps<{
  bookId: number;
  userId: number;
  modelValue: { value: string; label: string };
  totalPages?: number; 
  initialPage?: number; 
}>();

const emit = defineEmits(["update:modelValue", "progress-updated"]);

const statuses = [
  { value: "to_read", label: "Sẽ đọc" },
  { value: "currently_reading", label: "Đang đọc" },
  { value: "read", label: "Đã đọc" },
  { value: "dnf", label: "Chưa hoàn thành" },
];

async function updateBookStatus(newStatus: any) {
  emit("update:modelValue", newStatus);
  
  try {
    const statusValue = newStatus.value;
    
    if (statusValue === "rm_book") {
      await axios.delete(`${BOOK_SERVICE_URL}books/status/${props.userId}/${props.bookId}`);
      emit("update:modelValue", { value: "add_book", label: "Thêm vào kệ" });
    } else {
      await axios.put(`${BOOK_SERVICE_URL}books/${props.bookId}/status`, null, {
        params: { user_id: props.userId, status: statusValue },
      });
    }
  } catch (error) {
    console.error("Lỗi khi cập nhật trạng thái:", error);
  }
}

const buttonClass = computed(() => {
  if (props.modelValue.value === 'add_book') {
    return 'bg-gray-100 text-gray-700 hover:bg-gray-200';
  }
  return 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200';
});
</script>

<template>
  <div class="space-y-3">
      <!-- 1. PHẦN CHỌN TRẠNG THÁI -->
      <Listbox :modelValue="props.modelValue" @update:modelValue="updateBookStatus">
        <div class="relative w-full">
          <ListboxButton
            class="relative w-full cursor-default rounded-md py-1.5 pl-3 pr-10 text-left shadow-sm border"
            :class="buttonClass"
          >
            <span class="block truncate font-medium">
              {{ props.modelValue.label }}
            </span>
            <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
              <ChevronUpDownIcon class="h-5 w-5 text-gray-500" aria-hidden="true" />
            </span>
          </ListboxButton>

          <ListboxOptions
            class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
            
            <ListboxOption 
              v-for="status in statuses.filter(s => s.value !== props.modelValue.value)" 
              :key="status.value" 
              :value="status" 
              v-slot="{ active, selected }"
            >
              <li :class="[
                active ? 'bg-yellow-100 text-yellow-900' : 'text-gray-900',
                'relative cursor-default select-none py-2 pl-10 pr-4',
              ]">
                <span :class="[
                  selected ? 'font-medium' : 'font-normal',
                  'block truncate',
                ]">
                  {{ status.label }}
                </span>
                <span v-if="selected" class="absolute inset-y-0 left-0 flex items-center pl-3 text-yellow-600">
                  ✔
                </span>
              </li>
            </ListboxOption>
            
            <!-- Nút xóa sách khỏi kệ -->
            <li 
              v-if="props.modelValue.value !== 'add_book'"
              @click="updateBookStatus({ value: 'rm_book', label: 'Xóa sách' })"
              class="relative cursor-default select-none py-2 pl-10 pr-4 text-red-600 hover:bg-red-50 cursor-pointer"
            >
              Xóa sách khỏi kệ
            </li>
            
          </ListboxOptions>
        </div>
      </Listbox>
  </div>
</template>