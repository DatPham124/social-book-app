<script setup lang="ts">
import { ref, watch, computed } from 'vue'; // Thêm computed
import axios from "axios";
import { BOOK_SERVICE_URL } from "../../config.ts";
import { Listbox, ListboxButton, ListboxOption, ListboxOptions } from "@headlessui/vue";
import { ChevronUpDownIcon } from "@heroicons/vue/20/solid";

const props = defineProps<{
  bookId: number;
  userId: number;
  modelValue: { value: string; label: string };
}>();

const emit = defineEmits(["update:modelValue"]);

// 1. TÁCH BIỆT CÁC LỰA CHỌN
const statuses = [
  { value: "to_read", label: "Sẽ đọc" },
  { value: "currently_reading", label: "Đang đọc" },
  { value: "read", label: "Đã đọc" },
  { value: "dnf", label: "Chưa hoàn thành" },
];

// 2. HÀM GỌI API (Đã sửa)
async function updateBookStatus(newStatus: any) {
  // 3. Cập nhật UI ngay lập tức
  emit("update:modelValue", newStatus);
  
  try {
    const statusValue = newStatus.value;
    
    if (statusValue === "rm_book") {
      // 4. Xử lý logic XÓA (API của bạn đã có)
      await axios.delete(`${BOOK_SERVICE_URL}books/status/${props.userId}/${props.bookId}`);
      // Quay về trạng thái 'add_book'
      emit("update:modelValue", { value: "add_book", label: "Thêm vào kệ" });
    } else {
      // 5. Xử lý CẬP NHẬT/THÊM MỚI (API của bạn đã có)
      await axios.put(`${BOOK_SERVICE_URL}books/${props.bookId}/status`, null, {
        params: { user_id: props.userId, status: statusValue },
      });
    }
    
  } catch (error) {
    console.error("Lỗi khi cập nhật trạng thái:", error);
    // (Có thể thêm logic rollback nếu gọi API thất bại)
  }
}

// 6. LOGIC ĐỂ THAY ĐỔI MÀU SẮC NÚT BẤM
const buttonClass = computed(() => {
  if (props.modelValue.value === 'add_book') {
    return 'bg-gray-100 text-gray-700 hover:bg-gray-200'; // Màu Xám
  }
  return 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'; // Màu Vàng (giống component cũ của bạn)
});
</script>

<template>
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
        class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg">
        
        <!-- 7. CHỈ HIỂN THỊ CÁC LỰA CHỌN 'add_book' KHÔNG CÓ -->
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
        
        <!-- Nút Xóa (Chỉ hiện khi sách đã ở trên kệ) -->
        <li 
          v-if="props.modelValue.value !== 'add_book'"
          @click="updateBookStatus({ value: 'rm_book', label: 'Xóa sách' })"
          class="relative cursor-default select-none py-2 px-4 text-sm text-red-600 hover:bg-red-50"
        >
          Xóa sách khỏi kệ
        </li>
        
      </ListboxOptions>
    </div>
  </Listbox>
</template>
