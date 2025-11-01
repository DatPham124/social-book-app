<script setup lang="ts">
import Navbar from "../../layout/Navbar.vue";
import AddMeeting from "../BookClub/AddMeeting.vue";
import { ref, onMounted, computed } from "vue";
import BookClubForm from "../BookClub/BookClubForm.vue";
import { useRoute, useRouter } from "vue-router";
import axios from "axios";
// Sửa import - Thêm USER_SERVICE_URL và AVATAR_SERVER_URL
import { BOOK_SERVICE_URL, BOOKCLUB_IMAGE_SERVER_URL, USER_SERVICE_URL, AVATAR_SERVER_URL } from "../../../config";
import { getProfile } from "../../../composables/useProfile";
import { useAuth } from "../../../composables/useAuth";

// Interface cho User (dùng trong tìm kiếm)
interface SearchUser {
  id: number;
  username: string;
}

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

// 1. THÊM INTERFACE CHO THÀNH VIÊN
// Dữ liệu này sẽ được tổng hợp ở frontend
interface Member {
  user_id: number;
  role: string;
  username: string; // Lấy từ getProfile
  avatar_url?: string; // Lấy từ getProfile
}

const route = useRoute();
const router = useRouter();
const clubId = Number(route.params.id);
const { userInfo } = useAuth();

const club = ref<Club | null>(null);
const meetings = ref<Meeting[]>([]);
const activeTab = ref("upcoming");
const showAddMeeting = ref(false);

const showMenu = ref(false);
const showEdit = ref(false);

// Refs cho việc mời
const searchQuery = ref("");
const searchResults = ref<SearchUser[]>([]);
const isSearching = ref(false);
const inviteMessage = ref("");

// 2. THÊM REFS CHO THÀNH VIÊN
const memberCount = ref(0);
const membersList = ref<Member[]>([]); // Danh sách đầy đủ (có profile)

const isCreator = computed(() => {
  if (!userInfo.value || !club.value) return false;
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  return userId === club.value.creator_id;
});

async function searchUsers() {
  if (searchQuery.value.length < 2) {
    searchResults.value = [];
    return;
  }
  isSearching.value = true;
  inviteMessage.value = "";
  try {
    const res = await axios.get(`${USER_SERVICE_URL}users/search`, {
      params: { query: searchQuery.value },
    });
    const currentUserId = userInfo.value?.id || userInfo.value?.user_id;
    searchResults.value = res.data.filter((user: SearchUser) => user.id !== currentUserId);
  } catch (err) {
    console.error("Lỗi tìm user:", err);
  } finally {
    isSearching.value = false;
  }
}

async function sendInvite(inviteeId: number) {
  inviteMessage.value = "Đang gửi lời mời...";
  const creatorId = userInfo.value?.id || userInfo.value?.user_id;
  if (!creatorId) {
    inviteMessage.value = "Lỗi: Không tìm thấy người gửi.";
    return;
  }
  try {
    const formData = new FormData();
    formData.append("invitee_id", String(inviteeId));
    formData.append("creator_id", String(creatorId));
    await axios.post(
      `${BOOK_SERVICE_URL}bookclubs/${clubId}/invite`,
      formData
    );
    inviteMessage.value = "Đã gửi lời mời thành công!";
    searchResults.value = searchResults.value.filter(user => user.id !== inviteeId);
  } catch (err: any) {
    inviteMessage.value = err.response?.data?.detail || "Lỗi khi gửi lời mời";
  }
}

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

// 3. SỬA HÀM getMemberCount
async function getMemberCount(clubId: number) {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${clubId}/member-count`);
    return res.data; // Trả về { member_count: X }
  } catch (error) {
    console.error("Lỗi khi đếm thành viên:", error);
    return { member_count: 0 }; // Trả về 0 nếu lỗi
  }
}

// 4. SỬA HÀM getMembers ĐỂ LẤY PROFILE
async function getMembers(clubId: number) {
  try {
    // API này trả về List[BookClubMember] (chỉ có user_id, role)
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${clubId}/members`);

    // Dùng Promise.all để gọi getProfile cho từng user_id
    const membersWithProfile = await Promise.all(
      res.data.map(async (member: { user_id: number; role: string }) => {
        const profile = await getProfile(member.user_id);
        return {
          user_id: member.user_id,
          role: member.role,
          username: profile?.username || "Người dùng ẩn",
          avatar_url: profile?.avatar_url || null,
        };
      })
    );
    return membersWithProfile; // Trả về danh sách đã gộp profile

  } catch (error) {
    console.error("Lỗi khi lấy danh sách thành viên:", error);
    return [];
  }
}
// ---

function handleMeetingCreated() {
  showAddMeeting.value = false;
  loadData();
}

// 5. SỬA LẠI HOÀN CHỈNH HÀM LOADDATA
async function loadData() {
  // Lấy club trước
  const clubData = await getClub(clubId);
  if (clubData) {
    const profile = await getProfile(clubData.creator_id);
    club.value = { ...clubData, creator_name: profile.username };
  } else {
    return; // Dừng nếu không tìm thấy club
  }

  // Lấy (Meetings, Count, Member List) cùng lúc để tăng tốc
  const [meetingData, memberCountData, memberListData] = await Promise.all([
    getMeetings(clubId),
    getMemberCount(clubId),
    getMembers(clubId)
  ]);

  // Xử lý Meetings
  const now = new Date();
  meetings.value = (meetingData || []).map((m: any) => ({
    ...m,
    status: new Date(m.date) > now ? "upcoming" : "past",
  }));

  // Xử lý Member Count
  memberCount.value = memberCountData?.member_count || 0;

  // Xử lý Member List
  membersList.value = memberListData || [];
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
                <button v-if="isCreator" @click="openEditClub" class="block w-full text-left ...">
                  ✏️ Chỉnh sửa
                </button>
              </div>
            </div>
          </div>

          <p class="text-gray-600 mt-1">
            Người quản lý:
            <span class="font-semibold text-yellow-600">{{ club.creator_name }}</span>
          </p>

          <!-- 6. THÊM SỐ LƯỢNG THÀNH VIÊN VÀO HEADER -->
          <p class="text-gray-500 text-sm mt-1">
            {{ memberCount }} thành viên
          </p>

        </div>
      </div>

      <!-- 7. THÊM TAB "THÀNH VIÊN" -->
      <div class="flex space-x-6 mt-4 border-b border-gray-200">
        <button v-for="tab in [
          { key: 'upcoming', label: 'Cuộc họp sắp tới' },
          { key: 'past', label: 'Cuộc họp đã qua' },
          { key: 'members', label: 'Thành viên' },
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

              <button v-if="isCreator" @click="showAddMeeting = true" class="px-4 py-2 bg-yellow-400 ...">
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
              <div v-if="isCreator" class="flex justify-center mt-6">
                <button @click="showAddMeeting = true" class="px-4 py-2 bg-yellow-400 ...">
                  + Thêm cuộc họp
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- (Code tab 'past' giữ nguyên) -->
        <div v-else-if="activeTab === 'past'">
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

        <!-- 8. NỘI DUNG TAB "THÀNH VIÊN" -->
        <div v-else-if="activeTab === 'members'">

          <!-- Phần Mời (Chỉ Host thấy) -->
          <div v-if="isCreator" class="mb-8 p-4 bg-gray-50 rounded-lg border">
            <h3 class="text-lg font-semibold text-yellow-600 mb-3">Mời thành viên</h3>
            <input v-model="searchQuery" @input="searchUsers" type="text"
              class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
              placeholder="Tìm theo username..." />

            <div v-if="isSearching" class="text-gray-500 text-center py-3">Đang tìm...</div>

            <ul v-if="searchResults.length > 0" class="mt-4 max-h-60 overflow-y-auto space-y-2">
              <li v-for="user in searchResults" :key="user.id"
                class="flex justify-between items-center p-2 border rounded-md bg-white hover:bg-gray-100">
                <span class="font-medium text-gray-700">{{ user.username }}</span>
                <button @click="sendInvite(user.id)"
                  class="px-3 py-1 bg-yellow-400 hover:bg-yellow-500 text-black text-sm font-semibold rounded-md">
                  Mời
                </button>
              </li>
            </ul>
            <p v-if="inviteMessage" class="text-sm text-green-600 mt-3">{{ inviteMessage }}</p>
          </div>

          <!-- Phần Danh sách thành viên -->
          <div>
            <h3 class="text-lg font-semibold text-yellow-600 mb-3">
              Tất cả thành viên ({{ memberCount }})
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

              <!-- 9. SỬA LẠI VÒNG LẶP ĐỂ DÙNG ROUTER-LINK -->
              <router-link v-for="member in membersList" :key="member.user_id" :to="'/profile/' + member.user_id"
                class="flex items-center gap-3 p-3 bg-white border rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                <div
                  class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-700 overflow-hidden shadow-sm flex-shrink-0">
                  <template v-if="member.avatar_url">
                    <img :src="`${AVATAR_SERVER_URL}/${member.avatar_url}`" alt="Avatar"
                      class="w-full h-full object-cover" />
                  </template>
                  <template v-else>
                    {{ member.username?.charAt(0)?.toUpperCase() || "U" }}
                  </template>
                </div>
                <div>
                  <p class="font-semibold text-gray-800 hover:text-yellow-700">{{ member.username }}</p>
                  <span v-if="member.role === 'host'" class="text-xs text-yellow-600 font-medium">
                    Người quản lý
                  </span>
                  <span v-else class="text-xs text-gray-500">
                    Thành viên
                  </span>
                </div>
              </router-link>

            </div>
          </div>
        </div>

        <!-- (Code tab 'about' giữ nguyên) -->
        <div v-else-if="activeTab === 'about'">
          <div class="bg-gray-50 p-4 sm:p-5 rounded-lg border">
            <p class="whitespace-pre-line leading-relaxed text-gray-800">
              {{ club.description || "Chưa có mô tả cho câu lạc bộ này." }}
            </p>
          </div>
        </div>

        <!-- (Code tab 'rules' giữ nguyên) -->
        <div v-else-if="activeTab === 'rules'">
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
