<script setup lang="ts">
import { ref } from "vue";
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

const statuses = [
  { value: "to_read", label: "Sẽ đọc" },
  { value: "currently_reading", label: "Đang đọc" },
  { value: "read", label: "Đã đọc" },
  { value: "dnf", label: "Chưa hoàn thành" },
  { value: "rm_book", label: "Xóa sách" },
]

async function deleteBook(user_id: number, book_id: number) {
  try {
    const response = await axios.delete(`${BOOK_SERVICE_URL}books/status/${user_id}/${book_id}`)
  }
  catch (error) {
    console.error("Lỗi khi cập nhật trạng thái:", error);

  }
}

async function updateBookStatus(newStatus: any) {
  emit("update:modelValue", newStatus);
  try {

    if (newStatus.value === "rm_book"){
      await deleteBook(props.userId, props.bookId)
      return;
    }

    await axios.put(`${BOOK_SERVICE_URL}books/${props.bookId}/status`, null, {
      params: { user_id: props.userId, status: newStatus.value },
    });
  } catch (error) {
    console.error("Lỗi khi cập nhật trạng thái:", error);
  }
}
</script>

<template>
  <Listbox v-model="props.modelValue" @update:modelValue="updateBookStatus">
    <div class="relative w-full">
      <ListboxButton
        class="relative w-full cursor-default rounded-md bg-green-100 py-1.5 pl-3 pr-10 text-left text-green-700 shadow-sm">
        <span class="block truncate font-medium">
          {{ props.modelValue.label }}
        </span>
        <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
          <ChevronUpDownIcon class="h-5 w-5 text-green-700" aria-hidden="true" />
        </span>
      </ListboxButton>

      <ListboxOptions
        class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg">
        <ListboxOption v-for="status in statuses" :key="status.value" :value="status" v-slot="{ active, selected }">
          <li :class="[
            active ? 'bg-green-100 text-green-900' : 'text-gray-900',
            'relative cursor-default select-none py-2 pl-10 pr-4',
          ]">
            <span :class="[
              selected ? 'font-medium' : 'font-normal',
              'block truncate',
            ]">
              {{ status.label }}
            </span>
            <span v-if="selected" class="absolute inset-y-0 left-0 flex items-center pl-3 text-green-600">
              ✔
            </span>
          </li>
        </ListboxOption>
      </ListboxOptions>
    </div>
  </Listbox>
</template>
