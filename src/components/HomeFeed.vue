<script setup>
import { onMounted, ref, watch } from 'vue';
import axios from 'axios';
import { Listbox, ListboxButton, ListboxOption, ListboxOptions } from '@headlessui/vue'
import { ChevronUpDownIcon } from '@heroicons/vue/20/solid'

// Các trạng thái sách
const statuses = [
  { value: 'to_read', label: 'Sẽ đọc' },
  { value: 'currently_reading', label: 'Đang đọc' },
  { value: 'read', label: 'Đã đọc' },
  { value: 'dnf', label: 'Bỏ dở' }
]


const books = ref([]);
const errorMessages = ref("");

// Hàm gọi API update status (mock trước)
async function updateBookStatus(bookId, status) {
  try {
    await axios.put(`http://localhost:8001/books/${bookId}/status`, {
      status
    });
    console.log(`Book ${bookId} updated to status: ${status}`);
  } catch (error) {
    console.error("Lỗi khi cập nhật trạng thái:", error);
  }
}

async function getAuthor(authorID) {
  try {
    const response = await axios.get(`http://localhost:8001/author/${authorID}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      errorMessages.value = error.response.data.detail;
    } else {
      errorMessages.value = "Không thể kết nối đến server";
    }
  }
}

async function getCategory(categoryID) {
  try {
    const response = await axios.get(`http://localhost:8001/category/${categoryID}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      errorMessages.value = error.response.data.detail;
    } else {
      errorMessages.value = "Không thể kết nối đến server";
    }
  }
}

async function getBooks() {
  try {
    const response = await axios.get('http://localhost:8001/books/');
    const updatedBooks = await Promise.all(
      response.data.map(async (book) => {
        const [authorResponse, categoryResponse] = await Promise.all([
          getAuthor(book.authorID),
          getCategory(book.categoryID)
        ]);

        const authorName = authorResponse ? authorResponse.name : 'Không rõ';
        const categoryName = categoryResponse ? categoryResponse.name : 'Không rõ';

        // Gắn trạng thái mặc định (to_read), sau này có thể load từ API user_book_status
        const status = statuses[0];

        return { ...book, authorName, categoryName, status };
      })
    );
    books.value = updatedBooks;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      errorMessages.value = error.response.data.detail;
    } else {
      errorMessages.value = "Không thể kết nối đến server";
    }
  }
}

onMounted(() => {
  getBooks();
});
</script>

<template>
  <div>
    <div v-if="errorMessages" class="text-red-500 font-semibold text-center mt-4">
      {{ errorMessages }}
    </div>

    <ul v-else-if="books.length > 0">
      <li v-for="book in books" :key="book.id">
        <div class="flex flex-row relative h-60 w-full bg-white rounded-lg shadow-md m-2">
          <!-- Ảnh bìa -->
          <div class="relative h-full w-40 flex-shrink-0">
            <img :src="`http://34.9.73.53/uploads/${book.cover_url}`" alt="Book Cover"
              class="h-full object-contain" />
          </div>

          <!-- Thông tin sách -->
          <div class="m-4 flex-grow">
            <p class="font-bold text-2xl">{{ book.title }}</p>
            <p class="text-gray-600 mt-2">Tác giả: {{ book.authorName }}</p>
            <p class="text-gray-600 mt-2">Thể loại: {{ book.categoryName }}</p>
            <p class="text-gray-600 mt-2">Năm xuất bản: {{ book.published_date }}</p>
            <p class="text-gray-600 mt-2">Mô tả: {{ book.description }}</p>
          </div>

          <div class="p-4 flex items-start justify-end">
            <Listbox v-model="book.status" @update:modelValue="(val) => updateBookStatus(book.id, val.value)">
              <div class="relative w-48">
                <ListboxButton
                  class="relative w-full cursor-default rounded-md bg-yellow-400 py-2 pl-3 pr-10 text-left text-black shadow-md focus:outline-none focus:ring-2 focus:ring-yellow-500 sm:text-sm">
                  <span class="block truncate">{{ book.status.label }}</span>
                  <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                    <ChevronUpDownIcon class="h-5 w-5 text-black" aria-hidden="true" />
                  </span>
                </ListboxButton>

                <ListboxOptions
                  class="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-sm">
                  <ListboxOption
                    v-for="status in statuses"
                    :key="status.value"
                    :value="status"
                    v-slot="{ active, selected }">
                    <li
                      :class="[
                        active ? 'bg-yellow-100 text-yellow-900' : 'text-gray-900',
                        'relative cursor-default select-none py-2 pl-10 pr-4'
                      ]">
                      <span :class="[selected ? 'font-medium' : 'font-normal', 'block truncate']">
                        {{ status.label }}
                      </span>
                      <span
                        v-if="selected"
                        class="absolute inset-y-0 left-0 flex items-center pl-3 text-yellow-600">
                        ✔
                      </span>
                    </li>
                  </ListboxOption>
                </ListboxOptions>
              </div>
            </Listbox>
          </div>
        </div>
      </li>
    </ul>

    <div v-else class="text-center text-gray-500 mt-4">
      Đang tải sách hoặc không có sách nào được tìm thấy.
    </div>
  </div>
</template>
