<script setup lang="ts">
import Navbar from "../../layout/Navbar.vue";
import AddMeeting from "../BookClub/AddMeeting.vue";
import { ref, onMounted, computed } from "vue";
import BookClubForm from "../BookClub/BookClubForm.vue";
import { useRoute, useRouter } from "vue-router"; import axios from "axios";
import { BOOK_SERVICE_URL, BOOKCLUB_IMAGE_SERVER_URL } from "../../../config";
import { getProfile } from "../../../composables/useProfile";


interface Club {
  id: number;
  name: string;
  avatar_url?: string;
  creator_name: string;
  description?: string;
  rules?: string;
  creator_id?: number;
}

interface Meeting {
  id: number;
  title: string;
  date: string;
  status: "upcoming" | "past";
}

const route = useRoute();
const router = useRouter();
const clubId = Number(route.params.id);

const club = ref<Club | null>(null);
const meetings = ref<Meeting[]>([]);
const activeTab = ref("upcoming");
const showAddMeeting = ref(false);

const showMenu = ref(false);
const showEdit = ref(false);

function goToMeeting(id: number) {
  router.push(`/meeting/${id}`);
}

function openEditClub() {
  showEdit.value = true;
  showMenu.value = false;
}

function handleEditCancel() {
  showEdit.value = false;
}

async function handleEditSaved() {
  showEdit.value = false;
  await loadData();
}

const rulesList = computed(() => {
  if (!club.value || !club.value.rules) {
    return [];
  }

  return club.value.rules
    .split(/\r?\n/)
    .filter(line => line.trim() !== '')
    .map(line => line.replace(/^\d+\.\s*/, ''));
});

async function getClub(clubId: number) {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${clubId}`);
    return res.data;
  } catch (error) {
    console.error("Lỗi khi lấy thông tin câu lạc bộ:", error);
    return null;
  }
}

async function getMeetings(clubId: number) {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${clubId}/meetings`);
    return res.data;
  } catch (error) {
    console.error("Lỗi khi lấy danh sách cuộc họp:", error);
    return [];
  }
}

function handleMeetingCreated() {
  showAddMeeting.value = false;
  loadData();
}

async function loadData() {
  const clubData = await getClub(clubId);
  if (clubData) {
    const profile = await getProfile(clubData.creator_id);
    club.value = { ...clubData, creator_name: profile.username };
  }

  const meetingData = await getMeetings(clubId);
  const now = new Date();

  meetings.value = meetingData.map((m: any) => ({
    ...m,
    status: new Date(m.date) > now ? "upcoming" : "past",
  }));
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <Navbar />

  <div v-if="!club" class="text-center py-20 text-gray-500">
    Đang tải thông tin câu lạc bộ...
  </div>

  <div v-else class="max-w-5xl mx-auto mt-8 bg-white shadow rounded-xl p-6">
    <BookClubForm v-if="showEdit" :club-id="clubId" @saved="handleEditSaved" @cancel="handleEditCancel" />

    <div v-else>
      <div class="flex items-start gap-6 border-b pb-4 relative">
        <img v-if="club.avatar_url" :src="`${BOOKCLUB_IMAGE_SERVER_URL}/${club.avatar_url}`" alt="Avatar CLB"
          class="w-24 h-24 object-cover rounded-md border border-gray-300 shadow-sm" />
        <div v-else
          class="w-24 h-24 bg-gray-200 flex items-center justify-center rounded-md text-gray-500 font-bold text-2xl">
          {{ club.name.charAt(0).toUpperCase() }}
        </div>

        <div class="flex-1">
          <p class="text-sm font-semibold text-yellow-600 uppercase">Câu lạc bộ</p>
          <div class="flex items-center justify-between">
            <h2 class="text-2xl font-bold text-gray-800">{{ club.name }}</h2>

            <div class="relative">
              <button @click="showMenu = !showMenu" class="text-gray-500 hover:text-gray-700 text-2xl font-bold px-2">
                ⋮
              </button>

              <div v-if="showMenu" class="absolute right-0 mt-2 w-32 bg-white border rounded-md shadow-lg z-10">
                <button @click="openEditClub"
                  class="block w-full text-left px-3 py-2 text-sm hover:bg-yellow-50 rounded-md text-gray-700">
                  ✏️ Chỉnh sửa
                </button>
              </div>
            </div>
          </div>

          <p class="text-gray-600 mt-1">
            Người quản lý:
            <span class="font-semibold text-yellow-600">{{ club.creator_name }}</span>
          </p>
        </div>
      </div>

      <div class="flex space-x-6 mt-4 border-b border-gray-200">
        <button v-for="tab in [
          { key: 'upcoming', label: 'Cuộc họp sắp tới' },
          { key: 'past', label: 'Cuộc họp đã qua' },
          { key: 'about', label: 'Giới thiệu' },
          { key: 'rules', label: 'Nội quy' },
        ]" :key="tab.key" @click="activeTab = tab.key" class="py-2 text-sm font-medium transition-colors border-b-2"
          :class="activeTab === tab.key
            ? 'text-yellow-600 border-yellow-400'
            : 'text-gray-500 border-transparent hover:text-gray-700'
            ">
          {{ tab.label }}
        </button>
      </div>

      <div class="mt-6">
        <div v-if="activeTab === 'upcoming'">
          <div v-if="showAddMeeting">
            <AddMeeting :club-id="clubId" @created="handleMeetingCreated" @cancel="showAddMeeting = false" />
          </div>
          <div v-else>
            <div v-if="meetings.filter(m => m.status === 'upcoming').length === 0"
              class="text-center py-10 text-gray-500">
              <p class="font-semibold italic mb-3">Chưa có cuộc họp sắp tới</p>
              <button @click="showAddMeeting = true"
                class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md transition">
                + Tạo cuộc họp mới
              </button>
            </div>

            <div v-else class="space-y-4">
              <div v-for="meeting in meetings.filter(m => m.status === 'upcoming')" :key="meeting.id"
                class="p-4 border rounded-lg flex justify-between items-center hover:bg-gray-50 transition">
                <div>
                  <p class="font-semibold text-gray-800">{{ meeting.title }}</p>
                  <p class="text-sm text-gray-500">
                    Ngày: {{ new Date(meeting.date).toLocaleDateString() }},
                    Giờ:
                    {{
                      new Date(meeting.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    }}
                  </p>
                </div>
                <button @click="goToMeeting(meeting.id)"
                  class="px-3 py-1 bg-yellow-400 hover:bg-yellow-500 rounded-md text-black text-sm font-medium">
                  Chi tiết
                </button>
              </div>

              <div class="flex justify-center mt-6">
                <button @click="showAddMeeting = true"
                  class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md transition">
                  + Thêm cuộc họp
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'past'" class="space-y-4">
          <div v-if="meetings.filter(m => m.status === 'past').length === 0" class="text-center text-gray-500 py-10">
            <p>Chưa có cuộc họp nào trước đây.</p>
          </div>

          <div v-else>
            <div v-for="meeting in meetings.filter(m => m.status === 'past')" :key="meeting.id"
              class="p-4 my-4 border rounded-lg flex justify-between items-center hover:bg-gray-50 transition">
              <div>
                <p class="font-semibold text-gray-800">{{ meeting.title }}</p>
                <p class="text-sm text-gray-500">
                  Ngày: {{ new Date(meeting.date).toLocaleDateString() }},
                  Giờ:
                  {{
                    new Date(meeting.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                  }}
                </p>
              </div>
              <button @click="goToMeeting(meeting.id)"
                class="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-600 hover:bg-gray-100">
                Xem lại
              </button>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'about'" class="text-gray-700">
          <h3 class="text-lg font-semibold text-yellow-600 mb-3">Giới thiệu</h3>
          <div class="bg-gray-50 p-4 sm:p-5 rounded-lg border">
            <p class="whitespace-pre-line leading-relaxed text-gray-800">
              {{ club.description || "Chưa có mô tả cho câu lạc bộ này." }}
            </p>
          </div>
        </div>

        <div v-else-if="activeTab === 'rules'" class="text-gray-700">
          <h3 class="text-lg font-semibold text-yellow-600 mb-3">Nội quy</h3>

          <div v-if="rulesList.length > 0" class="bg-gray-50 p-4 sm:p-6 rounded-lg border">
            <ol class="list-decimal list-outside pl-5 space-y-2 text-gray-800 leading-relaxed">
              <li v-for="(rule, index) in rulesList" :key="index">
                {{ rule }}
              </li>
            </ol>
          </div>

          <div v-else class="text-center text-gray-500 py-10 italic">
            <p>Chưa có nội quy cho câu lạc bộ này.</p>
          </div>
        </div>
      </div>
    </div>
  </div>

</template>
