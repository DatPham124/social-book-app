<script setup lang="ts">
import { ref, onMounted } from 'vue';
import Navbar from '../components/layout/Navbar.vue';
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL, USER_SERVICE_URL } from '../config';
import { useAuth } from '../composables/useAuth';
import axios from 'axios';

interface Book {
  id: number;
  title: string;
  cover_url?: string;
}

const { userInfo } = useAuth();
const userId = userInfo.value?.id || userInfo.value?.user_id;

const loadingGenre = ref(true);
const loadingAuthor = ref(true);
const loadingFriends = ref(true);
const loadingAiRecs = ref(true);
const genreRecs = ref<Book[]>([]);
const authorRecs = ref<Book[]>([]);
const friendRecs = ref<Book[]>([]);
const aiRecs = ref<Book[]>([]);
const error = ref<string | null>(null);

async function loadRecsByGenre() {
  if (!userId) return;
  loadingGenre.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}ai/recommendations/by-genre/${userId}`);
    genreRecs.value = res.data;
  } catch (err: any) {
    console.error("Lỗi tải gợi ý theo thể loại:", err);
    if (!error.value) error.value = "Không thể tải gợi ý.";
  } finally {
    loadingGenre.value = false;
  }
}

async function loadRecsByAuthor() {
  if (!userId) return;
  loadingAuthor.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}ai/recommendations/by-author/${userId}`);
    authorRecs.value = res.data;
  } catch (err: any) {
    console.error("Lỗi tải gợi ý theo tác giả:", err);
  } finally {
    loadingAuthor.value = false;
  }
}

async function loadRecsByFriends() {
  if (!userId) return;
  loadingFriends.value = true;
  const token = localStorage.getItem("token");

  try {
    const friendListRes = await axios.get(
      `${USER_SERVICE_URL}friends/${userId}/accepted`,
      { headers: { Authorization: `Bearer ${token}` } }
    );

    const friendIds = friendListRes.data.map((friendship: any) => {
      return friendship.user_id === userId ? friendship.friend_id : friendship.user_id;
    });

    if (friendIds.length === 0) {
      friendRecs.value = [];
      loadingFriends.value = false;
      return;
    }

    const payload = {
      user_id: userId,
      friend_ids: friendIds
    };
    
    const res = await axios.post(`${BOOK_SERVICE_URL}ai/recommendations/by-friends`, payload);
    friendRecs.value = res.data;

  } catch (err: any) {
    console.error("Lỗi tải gợi ý từ bạn bè:", err);
    if (err.response?.status === 404) {
      friendRecs.value = []; 
    }
  } finally {
    loadingFriends.value = false;
  }
}

async function loadAiRecs() {
  if (!userId) return;
  loadingAiRecs.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}ai/recommendations/${userId}`);
    aiRecs.value = res.data;
  } catch (err: any) {
    console.error("Lỗi tải gợi ý AI:", err);
  } finally {
    loadingAiRecs.value = false;
  }
}

onMounted(() => {
  loadAiRecs();
  loadRecsByGenre();
  loadRecsByAuthor();
  loadRecsByFriends();
});

</script>

<template>
  <Navbar />
  <div class="w-full max-w-5xl mx-auto m-5 space-y-6 px-4">
    
    <h1 class="text-2xl font-logo text-yellow-400 item-center">Gợi ý cho bạn</h1>

    <div v-if="error" class="text-center text-red-500 py-10">
      {{ error }}
    </div>

    <div class="space-y-8">
      
      <section class="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">
          ✨ Gợi ý AI dành riêng cho bạn
        </h2>
        <div v-if="loadingAiRecs" class="text-center text-gray-500 py-5 italic">
          🤖 AI đang phân tích gu đọc của bạn...
        </div>
        <div v-else-if="aiRecs.length === 0" class="text-center text-gray-500 py-5 italic">
          (Chưa có đủ dữ liệu đọc. Hãy đọc thêm sách)
        </div>
        <div v-else class="flex gap-4 overflow-x-auto pb-4">
          <router-link
            v-for="book in aiRecs"
            :key="book.id"
            :to="{ name: 'book', params: { id: book.id } }"
            class="flex-shrink-0 w-32"
          >
            <img
              v-if="book.cover_url"
              :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`"
              :alt="book.title"
              class="w-full h-48 object-cover rounded shadow-md hover:shadow-lg transition-shadow"
            />
            <div v-else class="w-full h-48 bg-gray-100 rounded flex items-center justify-center text-3xl text-gray-400">📚</div>
            <h4 class="text-sm font-semibold truncate mt-2">{{ book.title }}</h4>
          </router-link>
        </div>
      </section>

      <section class="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">
          Vì bạn thích Thể loại...
        </h2>
        <div v-if="loadingGenre" class="text-center text-gray-500 py-5 italic">
          Đang tìm sách...
        </div>
        <div v-else-if="genreRecs.length === 0" class="text-center text-gray-500 py-5 italic">
          (Chưa có đủ dữ liệu đọc để gợi ý)
        </div>
        <div v-else class="flex gap-4 overflow-x-auto pb-4">
          <router-link
            v-for="book in genreRecs"
            :key="book.id"
            :to="{ name: 'book', params: { id: book.id } }"
            class="flex-shrink-0 w-32"
          >
            <img
              v-if="book.cover_url"
              :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`"
              :alt="book.title"
              class="w-full h-48 object-cover rounded shadow-md hover:shadow-lg transition-shadow"
            />
            <div v-else class="w-full h-48 bg-gray-100 rounded flex items-center justify-center text-3xl text-gray-400">📚</div>
            <h4 class="text-sm font-semibold truncate mt-2">{{ book.title }}</h4>
          </router-link>
        </div>
      </section>
      
      <section class="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">
          Vì bạn thích Tác giả...
        </h2>
        <div v-if="loadingAuthor" class="text-center text-gray-500 py-5 italic">
          Đang tìm sách...
        </div>
        <div v-else-if="authorRecs.length === 0" class="text-center text-gray-500 py-5 italic">
          (Chưa có đủ dữ liệu đọc để gợi ý)
        </div>
        <div v-else class="flex gap-4 overflow-x-auto pb-4">
          <router-link
            v-for="book in authorRecs"
            :key="book.id"
            :to="{ name: 'book', params: { id: book.id } }"
            class="flex-shrink-0 w-32"
          >
            <img
              v-if="book.cover_url"
              :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`"
              :alt="book.title"
              class="w-full h-48 object-cover rounded shadow-md hover:shadow-lg transition-shadow"
            />
            <div v-else class="w-full h-48 bg-gray-100 rounded flex items-center justify-center text-3xl text-gray-400">📚</div>
            <h4 class="text-sm font-semibold truncate mt-2">{{ book.title }}</h4>
          </router-link>
        </div>
      </section>

      <section class="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">
          Bạn bè của bạn cũng đọc
        </h2>
        <div v-if="loadingFriends" class="text-center text-gray-500 py-5 italic">
          Đang tìm sách...
        </div>
        <div v-else-if="friendRecs.length === 0" class="text-center text-gray-500 py-5 italic">
          (Bạn bè của bạn chưa đọc gì mà bạn chưa đọc)
        </div>
        <div v-else class="flex gap-4 overflow-x-auto pb-4">
          <router-link
            v-for="book in friendRecs"
            :key="book.id"
            :to="{ name: 'book', params: { id: book.id } }"
            class="flex-shrink-0 w-32"
          >
            <img
              v-if="book.cover_url"
              :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`"
              :alt="book.title"
              class="w-full h-48 object-cover rounded shadow-md hover:shadow-lg transition-shadow"
            />
            <div v-else class="w-full h-48 bg-gray-100 rounded flex items-center justify-center text-3xl text-gray-400">📚</div>
            <h4 class="text-sm font-semibold truncate mt-2">{{ book.title }}</h4>
          </router-link>
        </div>
      </section>
      
    </div>
  </div>
</template>