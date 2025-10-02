<script setup lang="ts">
import { onMounted, ref } from 'vue';
import axios from 'axios';
import { Listbox, ListboxButton, ListboxOption, ListboxOptions } from '@headlessui/vue';
import { ChevronUpDownIcon } from '@heroicons/vue/20/solid';
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL } from '../../config.ts';
import { jwtDecode } from 'jwt-decode';

// -------- Props --------
const props = defineProps<{
  status: "to_read" | "currently_reading" | "read" | "dnf"; // trạng thái muốn hiển thị
  title: string; // tiêu đề hiển thị
}>();

// -------- State --------
const token = localStorage.getItem("token")
let userInfo: any = null
const books = ref<any[]>([])
const loading = ref(true)
const errorMessages = ref("")
const isSaving = ref(false)

const statuses = [
  { value: 'to_read', label: 'Sẽ đọc' },
  { value: 'currently_reading', label: 'Đang đọc' },
  { value: 'read', label: 'Đã đọc' },
  { value: 'dnf', label: 'Chưa hoàn thành' }
]

// -------- Decode token --------
if (token) {
  try {
    userInfo = jwtDecode<any>(token);
    if (userInfo.exp * 1000 < Date.now()) {
      localStorage.removeItem('token');
      userInfo = null;
    }
  } catch {
    localStorage.removeItem('token');
  }
}

// -------- Helper functions --------
async function getReadingProgress(userId: number, bookId: number) {
  try {
    const respone = await axios.get(`${BOOK_SERVICE_URL}books/reading-progress/${userId}/${bookId}`);
    return respone.data;
  }
  catch (error) {
    console.error("Lỗi khi lấy tiến độ:", error);
    return null;
  }
}

async function updateReadingProgress(book: any, newPage: number) {
  isSaving.value = true
  try {
    await axios.put(
      `${BOOK_SERVICE_URL}books/reading-progress/${userInfo?.user_id}/${book.id}`,
      null,
      { params: { current_page_from_user: newPage } }
    );

    // Cập nhật local state
    book.current_page = newPage;
    book.progress_percentage = book.total_pages > 0
      ? Math.round((book.current_page / book.total_pages) * 100)
      : 0;
  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        alert(error.response.data.detail || "Có lỗi xảy ra khi cập nhật tiến độ");
      } else {
        alert("Không thể kết nối đến server, vui lòng thử lại sau");
      }
    } else {
      alert("Lỗi không xác định");
    }
  } finally {
    book.isSaving = false;
  }
}

async function getCategoryLink(bookId: number) {
  try {
    const category_list = await axios.get(`${BOOK_SERVICE_URL}category/book-category-link/book/${bookId}`);
    return category_list.data;
  }
  catch (error) {
    console.error("Lỗi khi lấy liên kết thể loại: ", error);
    return null;
  }
}

async function getCategory(category_id: number) {
  try {
    const respone = await axios.get(`${BOOK_SERVICE_URL}category/${category_id}`);
    return respone.data
  }
  catch (error) {
    console.error("Lỗi khi lấy thể loại: ", error);
    return null;
  }
}

function mapStatus(statusStr: string) {
  return statuses.find(s => s.value === statusStr) || statuses[0];
}

async function updateBookStatus(bookId: number, newStatus: any) {
  try {
    await axios.put(`${BOOK_SERVICE_URL}books/${bookId}/status`, null, {
      params: { user_id: userInfo?.user_id, status: newStatus.value }
    });
  } catch (error) {
    console.error("Lỗi khi cập nhật trạng thái:", error);
  }
}

async function fetchBooks() {
  if (!userInfo) {
    errorMessages.value = "Vui lòng đăng nhập để xem danh sách";
    loading.value = false;
    return;
  }

  try {
    loading.value = true;
    const response = await axios.get(
      `${BOOK_SERVICE_URL}books/status/book/${userInfo.user_id}`,
      { params: { status: props.status } }
    );

    const booksWithDetails = await Promise.all(
      response.data.map(async (userBook: any) => {
        const bookResponse = await axios.get(`${BOOK_SERVICE_URL}books/${userBook.book_id}`);
        const book = bookResponse.data;

        const authorName = "Không xác định";
        const progressData = await getReadingProgress(userInfo.user_id, userBook.book_id);

        let categoryName = "Không xác định"
        const categoryLink = await getCategoryLink(userBook.book_id);
        if (Array.isArray(categoryLink) && categoryLink.length > 0) {
          const categories = await Promise.all(
            categoryLink.map((cl: any) => getCategory(cl.category_id))
          );
          categoryName = categories
            .filter(c => c)
            .map(c => c.name)
            .join(', ');
        }

        const current_page = progressData?.current_page || 0;
        const total_pages = progressData?.total_pages || book.page_count || 0;
        const progress_percentage = total_pages > 0
          ? Math.round((current_page / total_pages) * 100)
          : 0;

        return {
          ...book,
          isSaving: false,
          authorName,
          categoryName,
          start_date: userBook.start_date,
          current_page,
          total_pages,
          progress_percentage,
          status: mapStatus(userBook.status),
          editingProgress: false,
          newPage: current_page,
        };
      })
    );

    books.value = booksWithDetails;
  } catch {
    errorMessages.value = "Không thể tải danh sách";
  } finally {
    loading.value = false;
  }
}

function formatDate(dateString: string) {
  if (!dateString) return 'Chưa xác định';
  return new Date(dateString).toLocaleDateString('vi-VN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

onMounted(() => {
  fetchBooks();
});
</script>

<template>
  <div class="max-w-3xl mx-auto p-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-logo text-yellow-400 item-center">{{ props.title }}</h1>
      <router-link v-if="props.status === 'currently_reading'" to="/reading-journal" class="px-4 py-1 rounded-md border bg-white hover:bg-yellow-200 text-sm">
        Xem nhật ký
      </router-link>
      <router-link v-if="props.status === 'read'" to="/reading-journal" class="px-4 py-1 rounded-md border bg-white hover:bg-yellow-200 text-sm">
        Xem sách chưa hoàn thành
      </router-link>
    </div>

    <p class="text-gray-500 text-sm mb-6">
      {{ books.length }} sách
    </p>

    <div v-if="loading" class="text-center py-8">
      <p class="text-gray-500">Đang tải sách...</p>
    </div>

    <div v-else-if="errorMessages" class="text-red-500 text-center py-8">
      {{ errorMessages }}
    </div>

    <div v-else-if="books.length === 0" class="text-center py-8">
      <p class="text-gray-500">Không có sách nào</p>
      <router-link to="/explore" class="text-yellow-500 hover:text-yellow-600 mt-2 inline-block">
        Khám phá sách mới →
      </router-link>
    </div>

    <div v-else>
      <div v-for="book in books" :key="book.id" class="flex border rounded-xl shadow-sm mb-6 bg-white">
        <div class="w-32 h-52 flex-shrink-0">
          <img :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" :alt="book.title"
            class="w-full h-full object-cover rounded-l-xl" />
        </div>

        <div class="flex flex-grow p-4">
          <!-- Bên trái -->
          <div class="flex-grow pr-6 border-r border-gray-100 min-w-0">
            <h3 class="font-bold text-lg mb-0.5 text-gray-800">{{ book.title }}</h3>
            <p class="text-gray-600 text-sm mb-1">{{ book.authorName }}</p>
            <p class="text-gray-500 text-xs mb-3">
              {{ book.page_count }} trang • {{ book.language }} • {{ new Date(book.published_date).getFullYear() }}
            </p>
            <div class="flex flex-wrap gap-2 mb-4">
              <span v-for="category in book.categoryName.split(', ')" :key="category"
                class="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">
                {{ category.trim() }}
              </span>
            </div>
            <p class="text-xs text-gray-500 mt-auto">
              Bắt đầu đọc: {{ formatDate(book.start_date) }}
            </p>
          </div>

          <!-- Bên phải -->
          <div class="w-56 pl-6 flex flex-col justify-between items-start flex-shrink-0">
            <div class="w-full mb-3 relative" v-if="props.status === 'currently_reading'">
              <div class="flex justify-between items-center text-sm text-gray-600 mb-1 relative">
                <span>Tiến độ: {{ book.current_page }}/{{ book.total_pages }} trang</span>
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-yellow-600">{{ book.progress_percentage }}%</span>
                  <button @click="book.editingProgress = !book.editingProgress"
                    class="text-gray-400 hover:text-yellow-600 transition-colors p-1" title="Cập nhật tiến độ">
                    ✏️
                  </button>
                </div>
              </div>

              <div class="w-full bg-gray-200 rounded-full h-2.5">
                <div class="bg-yellow-400 h-2.5 rounded-full transition-all duration-500"
                  :style="{ width: `${book.progress_percentage}%` }"></div>
              </div>

              <div v-if="book.editingProgress" class="mt-2 flex gap-2">
                <input type="number" v-model.number="book.newPage" min="0" :max="book.total_pages"
                  class="w-20 border rounded px-2 py-1 text-sm" />
                <button @click="updateReadingProgress(book, book.newPage)"
                  class="px-2 py-1 bg-yellow-400 text-white rounded text-sm hover:bg-yellow-500" :disabled="isSaving">
                  <span v-if="isSaving">Đang lưu...</span>
                  <span v-else>Lưu</span>
                </button>
              </div>
            </div>

            <div class="mb-3 w-full">
              <Listbox v-model="book.status" @update:modelValue="(val) => updateBookStatus(book.id, val)">
                <div class="relative w-full">
                  <ListboxButton
                    class="relative w-full cursor-default rounded-md bg-green-100 py-1.5 pl-3 pr-10 text-left text-green-700 shadow-sm">
                    <span class="block truncate font-medium">{{ book.status.label }}</span>
                    <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                      <ChevronUpDownIcon class="h-5 w-5 text-green-700" aria-hidden="true" />
                    </span>
                  </ListboxButton>

                  <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg">
                    <ListboxOption v-for="status in statuses" :key="status.value" :value="status"
                      v-slot="{ active, selected }">
                      <li :class="[ active ? 'bg-green-100 text-green-900' : 'text-gray-900', 'relative cursor-default select-none py-2 pl-10 pr-4' ]">
                        <span :class="[ selected ? 'font-medium' : 'font-normal', 'block truncate']">
                          {{ status.label }}
                        </span>
                        <span v-if="selected" class="absolute inset-y-0 left-0 flex items-center pl-3 text-green-600">✔</span>
                      </li>
                    </ListboxOption>
                  </ListboxOptions>
                </div>
              </Listbox>
            </div>

            <div class="flex flex-col gap-2 w-full mt-auto">
              <button @click="updateBookStatus(book.id, mapStatus('read'))"
                class="text-sm text-yellow-600 hover:text-yellow-700 font-medium text-left" v-if="props.status === 'currently_reading'">
                → Đánh dấu "Đã đọc"
              </button>
              <button @click="updateBookStatus(book.id, mapStatus('dnf'))"
                class="text-sm text-gray-500 hover:text-gray-700 text-left" v-if="props.status === 'currently_reading'">
                → Đánh dấu "Chưa hoàn thành"
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
