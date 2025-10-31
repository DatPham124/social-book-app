<script setup lang="ts">
import { ref, onMounted, Ref, computed } from "vue";
import axios from "axios";
import { BOOK_SERVICE_URL } from "../../../config";
import { useAuth } from "../../../composables/useAuth";
import { useRoute } from "vue-router";
import Navbar from "../../layout/Navbar.vue";
import { useBooks } from "../../../composables/useBook";
import { COVER_IMAGE_SERVER_URL } from "../../../config";

const route = useRoute();
const meetingId = Number(route.params.id);

const { fetchBook } = useBooks();

interface Book {
  id: number;
  title: string;
  cover_url?: string;
  author?: string;
  categories?: string[];
}

interface Meeting {
  id: number;
  title: string;
  date: string;
  location?: string;
  agenda?: string;
  book_id?: number;
  book?: Book; 
  creator_id?: number;
}

const meeting: Ref<Meeting | null> = ref(null);
const loading = ref(true);
const { userInfo } = useAuth();

const isEditingAgenda = ref(false);
const editedAgenda = ref("");
const isSavingAgenda = ref(false);

const isCreator = computed(() => {
  if (!userInfo.value || !meeting.value) return false;
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  return userId === meeting.value.creator_id;
});

async function loadMeetingDetails() {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/meeting/${meetingId}`);
    meeting.value = res.data;
    editedAgenda.value = res.data.agenda || "";
  } catch (error) {
    console.error("Lỗi tải chi tiết cuộc họp:", error);
  }
}

function startEditAgenda() {
  isEditingAgenda.value = true;
}

function cancelEditAgenda() {
  isEditingAgenda.value = false;
  editedAgenda.value = meeting.value?.agenda || "";
}

async function saveAgenda() {
  isSavingAgenda.value = true;
  try {
    const formData = new FormData();
    formData.append("agenda", editedAgenda.value);

    await axios.put(
      `${BOOK_SERVICE_URL}bookclubs/meeting/${meetingId}/agenda`,
      formData
    );


    if (meeting.value) {
      meeting.value.agenda = editedAgenda.value;
    }
    
    isEditingAgenda.value = false;
    
  } catch (error) {
    console.error("Lỗi lưu agenda:", error);
    alert("Lưu thất bại!");
  } finally {
    isSavingAgenda.value = false;
  }
}

onMounted(async () => {
  loading.value = true;
  await loadMeetingDetails();

  console.log(meeting.value?.book_id)

  if (meeting.value && meeting.value.book_id) {
    const bookData = await fetchBook(meeting.value.book_id);
    if (bookData) {
      meeting.value.book = bookData;
    }
  }

  loading.value = false;
});
</script>

<template>
  <Navbar />

  <div class="max-w-5xl mx-auto p-4 sm:p-6 mt-2">
    <div v-if="loading" class="text-center text-gray-500 text-lg py-10">Đang tải chi tiết...</div>

    <div v-else-if="!meeting" class="bg-white p-6 rounded-lg text-red-500 text-center">
      Không tìm thấy cuộc họp.
    </div>

    <div v-else class="bg-white rounded-lg shadow-xl w-full flex flex-col">
      <div class="border-b p-4 sm:p-5 relative">
        <p class="text-sm font-semibold text-yellow-600">CHI TIẾT CUỘC HỌP</p>
        <h2 class="text-2xl font-bold text-gray-800 mt-1">{{ meeting.title }}</h2>

        <div class="flex items-center text-gray-600 mt-2 space-x-4">
          <div class="flex items-center">
            <span class="mr-2 text-lg">🗓️</span>
            <span>{{ new Date(meeting.date).toLocaleString('vi-VN', { dateStyle: 'long', timeStyle: 'short' })
              }}</span>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-4 sm:p-5 space-y-6">
        <div>
          <h3 class="text-lg font-semibold text-gray-700 mb-2">Sách thảo luận</h3>
          <div v-if="meeting.book" class="flex items-center gap-4 bg-gray-50 p-3 rounded-lg border">
            <img 
              v-if="meeting.book.cover_url"
              :src="`${COVER_IMAGE_SERVER_URL}/${meeting.book.cover_url}`" 
              :alt="meeting.book.title"
              class="w-12 h-16 object-cover rounded shadow-sm"
            />
            <div v-else class="w-12 h-16 bg-gray-200 rounded flex items-center justify-center text-lg">📚</div>
            
            <div>
              <p class="font-semibold text-gray-800">{{ meeting.book.title }}</p>
              <p class="text-sm text-gray-500">{{ meeting.book.author }}</p>
            </div>
          </div>
          <div v-else class="text-gray-500 italic bg-gray-50 p-3 rounded-lg border">
            Chưa chọn sách cho cuộc họp này.
          </div>
        </div>

        <div>
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-lg font-semibold text-gray-700">Chương trình họp / Ghi chú</h3>
            <div v-if="isCreator">
              <button v-if="!isEditingAgenda" @click="startEditAgenda"
                class="text-sm text-yellow-600 hover:text-yellow-800 font-medium">
                Chỉnh sửa
              </button>
            </div>
          </div>

          <div v-if="isEditingAgenda && isCreator">
            <textarea v-model="editedAgenda" rows="8"
              class="w-full border border-gray-300 rounded-md p-3 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
              placeholder="Nhấn vào đây để thêm ghi chú hoặc chương trình họp..."></textarea>
            <div class="flex justify-end gap-3 mt-3">
              <button @click="cancelEditAgenda"
                class="px-3 py-1 border border-gray-400 rounded-md text-gray-600 hover:bg-gray-100">
                Hủy
              </button>
              <button @click="saveAgenda" :disabled="isSavingAgenda"
                class="px-3 py-1 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md disabled:opacity-50">
                {{ isSavingAgenda ? 'Đang lưu...' : 'Lưu' }}
              </button>
            </div>
          </div>

          <div v-else>
            <div class="bg-gray-50 p-4 rounded-lg border min-h-[100px]">
              <p v-if="meeting.agenda" class="text-gray-800 whitespace-pre-line leading-relaxed">
                {{ meeting.agenda }}
              </p>
              <p v-else class="text-gray-500 italic">
                {{ isCreator ? 'Chưa có ghi chú. Bấm "Chỉnh sửa" để thêm.' : 'Chưa có ghi chú hay chương trình họp nào.' }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>