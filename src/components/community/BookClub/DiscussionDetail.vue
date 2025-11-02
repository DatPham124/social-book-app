<script setup lang="ts">
import { ref, onMounted, Ref } from "vue";
import axios from "axios";
import { BOOK_SERVICE_URL, AVATAR_SERVER_URL } from "../../../config";
import { useAuth } from "../../../composables/useAuth";
import { getProfile } from "../../../composables/useProfile";
import { useRoute, useRouter } from "vue-router";
import Navbar from "../../layout/Navbar.vue";

const route = useRoute();
const router = useRouter();
const discussionId = Number(route.params.id);

const { userInfo } = useAuth();

// --- Interfaces ---
interface Profile {
  username: string;
  avatar_url?: string;
}
interface Discussion {
  id: number;
  title: string;
  content: string;
  user_id: number;
  created_at: string;
  club_id: number;
  user?: Profile; // Profile người đăng
}
interface Comment {
  id: number;
  content: string;
  created_at: string;
  user_id: number;
  user?: Profile; // Profile người bình luận
}

// --- State ---
const discussion = ref<Discussion | null>(null);
const comments = ref<Comment[]>([]);
const newComment = ref("");
const loading = ref(true);
const isPostingComment = ref(false);

// --- API Functions ---
async function loadDiscussion() {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/discussion/${discussionId}`);
    const post = res.data;
    
    const profile = await getProfile(post.user_id);
    discussion.value = { ...post, user: profile };
    
  } catch (error) {
    console.error("Lỗi tải thảo luận:", error);
  }
}

async function loadComments() {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/discussion/${discussionId}/comments`);
    
    const commentsWithProfile = await Promise.all(
      res.data.map(async (comment: Comment) => {
        const profile = await getProfile(comment.user_id);
        return { ...comment, user: profile };
      })
    );
    comments.value = commentsWithProfile;
    
  } catch (error) {
    console.error("Lỗi tải bình luận:", error);
  }
}

async function postComment() {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!newComment.value.trim() || !userId) return;

  isPostingComment.value = true;
  try {
    const formData = new FormData();
    formData.append("content", newComment.value);
    formData.append("user_id", String(userId));

    await axios.post(
      `${BOOK_SERVICE_URL}bookclubs/discussion/${discussionId}/comment`, 
      formData
    );
    
    newComment.value = "";
    await loadComments(); 
  } catch (err: any) {
    alert(err.response?.data?.detail || "Lỗi khi đăng bình luận");
  } finally {
    isPostingComment.value = false;
  }
}

onMounted(async () => {
  loading.value = true;
  await Promise.all([
    loadDiscussion(),
    loadComments()
  ]);
  loading.value = false;
});
</script>

<template>
  <Navbar />
  <div class="max-w-3xl mx-auto p-4 sm:p-6 mt-8">
    <div v-if="loading" class="text-center text-gray-500 py-10">Đang tải...</div>
    
    <div v-else-if="!discussion" class="text-center text-red-500 py-10">
      Không tìm thấy bài thảo luận.
    </div>

    <div v-else>
      <button @click="router.push(`/bookclubs/${discussion.club_id}`)" 
        class="text-sm font-medium text-yellow-600 hover:text-yellow-800 mb-4">
        &larr; Quay lại Thảo luận
      </button>

      <div class="bg-white p-5 border rounded-lg shadow-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-700 overflow-hidden shadow-sm">
              <img v-if="discussion.user?.avatar_url" 
                :src="`${AVATAR_SERVER_URL}/${discussion.user.avatar_url}`" 
                class="w-full h-full object-cover" />
              <span v-else class="text-lg">
                {{ discussion.user?.username.charAt(0).toUpperCase() || 'A' }}
              </span>
            </div>
            <div>
              <p class="font-semibold text-gray-800">{{ discussion.user?.username }}</p>
              <p class="text-sm text-gray-500">{{ new Date(discussion.created_at).toLocaleString('vi-VN') }}</p>
            </div>
          </div>
          </div>

        <h2 class="text-2xl font-bold text-gray-900 mt-4">{{ discussion.title }}</h2>
        <p class="text-gray-700 mt-2 whitespace-pre-line">{{ discussion.content }}</p>
      </div>

      <div class="mt-8">
        <h3 class="text-lg font-semibold text-gray-700 mb-4">
          Bình luận ({{ comments.length }})
        </h3>
        
        <div v-if="comments.length === 0" class="text-center text-gray-500 py-10 italic">
          Chưa có bình luận nào.
        </div>

        <div v-else class="space-y-4">
          <div v-for="comment in comments" :key="comment.id" class="flex gap-3">
            <div class="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center font-semibold text-yellow-600 overflow-hidden flex-shrink-0">
              <img v-if="comment.user?.avatar_url" 
                   :src="`${AVATAR_SERVER_URL}/${comment.user.avatar_url}`"
                   class="w-full h-full object-cover" />
              <span v-else class="text-sm">
                {{ comment.user?.username.charAt(0).toUpperCase() || 'A' }}
              </span>
            </div>
            <div class="flex-1 bg-gray-50 rounded-lg p-3 border">
              <p class="text-sm">
                <span class="font-semibold text-gray-800">{{ comment.user?.username }}</span>
                <span class="text-gray-400 ml-2 text-xs">
                  {{ new Date(comment.created_at).toLocaleString('vi-VN') }}
                </span>
              </p>
              <p class="text-gray-700 whitespace-pre-line mt-1">{{ comment.content }}</p>
            </div>
          </div>
        </div>

        <div class="mt-6 border-t pt-6">
          <h4 class="font-semibold text-gray-700 mb-2">Thêm bình luận</h4>
          <textarea
            v-model="newComment"
            rows="3"
            class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
            placeholder="Viết bình luận của bạn..."
          ></textarea>
          <button
            @click="postComment"
            :disabled="isPostingComment"
            class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md mt-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isPostingComment ? 'Đang gửi...' : 'Gửi bình luận' }}
          </button>
        </div>
      </div>

    </div>
  </div>
</template>
