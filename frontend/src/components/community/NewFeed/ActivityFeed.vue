<script setup lang="ts">
import { ref, onMounted, Ref } from 'vue';
import axios from 'axios';
import { USER_SERVICE_URL, BOOK_SERVICE_URL, REVIEW_SERVICE_URL, COVER_IMAGE_SERVER_URL, AVATAR_SERVER_URL } from '../../../config';
import { useAuth } from '../../../composables/useAuth';
import { useBooks } from '../../../composables/useBook'; // Sửa lỗi typo
import { getProfile } from '../../../composables/useProfile';
import { useRouter } from 'vue-router';

const { userInfo } = useAuth();
const { getBookById } = useBooks();
const router = useRouter();

// Interface cho các item sau khi gộp
interface FeedItem {
  type: 'status' | 'review';
  date: string;
  user: { user_id: number, username: string, avatar_url?: string };
  book: { id: number, title: string, cover_url?: string, author?: string }; 
  status?: string; 
  rating?: number; 
  content?: string; 
}

const feedItems: Ref<FeedItem[]> = ref([]);
const loading = ref(true);
const error = ref<string | null>(null);

async function loadFriendFeed() {
  loading.value = true;
  error.value = null;
  const userId = userInfo.value?.id || userInfo.value?.user_id;

  if (!userId) {
    error.value = "Lỗi xác thực người dùng.";
    loading.value = false;
    return;
  }

  try {
    const token = localStorage.getItem("token");
    const friendRes = await axios.get(
      `${USER_SERVICE_URL}friends/${userId}/accepted`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    const friendIds = friendRes.data.map((f: any) => (f.user_id === userId ? f.friend_id : f.user_id));
    friendIds.push(userId); 

    const statusPromise = axios.get(`${BOOK_SERVICE_URL}books/feed/recent-status?limit=50`);
    const reviewPromise = axios.get(`${REVIEW_SERVICE_URL}review/feed/recent?limit=50`);
    
    const [statusRes, reviewRes] = await Promise.all([statusPromise, reviewPromise]);

    const friendStatusUpdates = statusRes.data.filter((item: any) => friendIds.includes(item.user_id));
    const friendReviews = reviewRes.data.filter((item: any) => friendIds.includes(item.user_id));

    const enrichedStatus = await Promise.all(
      friendStatusUpdates.map(async (item: any) => {
        const [profile, book] = await Promise.all([
          getProfile(item.user_id),
          getBookById(item.book_id)
        ]);
        return {
          type: 'status',
          date: item.updated_at,
          user: profile || { user_id: item.user_id, username: 'Người dùng ẩn' }, 
          book: book || { id: item.book_id, title: 'Sách không rõ' }, 
          status: item.status
        };
      })
    );

    const enrichedReviews = await Promise.all(
      friendReviews.map(async (item: any) => {
        const [profile, book] = await Promise.all([
          getProfile(item.user_id),
          getBookById(item.book_id)
        ]);
        return {
          type: 'review',
          date: item.created_at,
          user: profile || { user_id: item.user_id, username: 'Người dùng ẩn' },
          book: book || { id: item.book_id, title: 'Sách không rõ' },
          rating: item.rating,
          content: item.content
        };
      })
    );

    const combinedFeed = [...enrichedStatus, ...enrichedReviews];
    
    combinedFeed.sort((a, b) => new Date(b.date + "Z").getTime() - new Date(a.date + "Z").getTime());
    
    feedItems.value = combinedFeed as FeedItem[];

  } catch (err) {
    console.error(err);
    error.value = "Không thể tải bản tin.";
  } finally {
    loading.value = false;
  }
}

function goToProfile(userId: number) {
  router.push(`/profile/${userId}`);
}
function goToBook(bookId: number) {
  router.push(`/book/${bookId}`);
}

function formatTime(dateString: string) {
  const diffMs = Date.now() - new Date(dateString + "Z").getTime();
  const phut = Math.floor(diffMs / 60000);
  if (phut < 1) return "vừa xong";
  if (phut < 60) return `${phut} phút trước`;
  const gio = Math.floor(phut / 60);
  if (gio < 24) return `${gio} giờ trước`;
  const ngay = Math.floor(gio / 24);
  return `${ngay} ngày trước`;
}

onMounted(loadFriendFeed);
</script>

<template>
  <div>
    <div v-if="loading" class="text-center text-gray-500 py-10">
      Đang tải bản tin...
    </div>
    <div v-else-if="error" class="text-center text-red-500 py-10">
      {{ error }}
    </div>
    <div v-else-if="feedItems.length === 0" class="text-center text-gray-500 py-10">
      Bản tin của bạn bè đang trống.
    </div>

    <div v-else class="space-y-6">
      <div v-for="(item, index) in feedItems" :key="index" class="bg-white p-5 rounded-lg shadow border">
        
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div @click="goToProfile(item.user.user_id)"
                 class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-700 overflow-hidden shadow-sm flex-shrink-0 cursor-pointer">
              <img v-if="item.user.avatar_url" :src="`${AVATAR_SERVER_URL}/${item.user.avatar_url}`" class="w-full h-full object-cover" />
              <span v-else>{{ item.user.username?.charAt(0)?.toUpperCase() || 'U' }}</span>
            </div>
            <p class="text-gray-700">
              <span @click="goToProfile(item.user.user_id)" class="font-semibold cursor-pointer hover:text-yellow-600">
                {{ item.user.username }}
              </span>
              
              <span v-if="item.type === 'status' && item.status === 'currently_reading'">
                vừa bắt đầu đọc:
              </span>
              <span v-if="item.type === 'status' && item.status === 'read'">
                vừa đọc xong:
              </span>
              <span v-if="item.type === 'review'">
                vừa đánh giá sách:
              </span>
            </p>
          </div>
          <p class="text-sm text-gray-400 flex-shrink-0 ml-4">{{ formatTime(item.date) }}</p>
        </div>

        <div class="flex gap-4 mt-4 ml-13"> 
          <img 
            v-if="item.book.cover_url"
            :src="`${COVER_IMAGE_SERVER_URL}/${item.book.cover_url}`" 
            @click="goToBook(item.book.id)"
            class="w-20 h-28 object-cover rounded shadow-sm cursor-pointer"
          />
          <div v-else class="w-20 h-28 bg-gray-200 rounded flex items-center justify-center text-3xl">📚</div>
          
          <div class="flex-1">
            <h3 
              @click="goToBook(item.book.id)" 
              class="text-lg font-semibold text-gray-800 cursor-pointer hover:text-yellow-600"
            >
              {{ item.book.title }}
            </h3>
            <p class="text-sm text-gray-500">{{ item.book.author }}</p>

            <div v-if="item.type === 'review' && item.rating" class="mt-2">
              <p class="text-lg font-medium text-yellow-500">
                <span v-for="i in Math.floor(item.rating)" :key="i">⭐️</span>
              </p>
              <p v-if="item.content" class="text-gray-700 mt-1 italic whitespace-pre-line">
                "{{ item.content }}"
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
