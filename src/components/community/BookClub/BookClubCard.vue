<script setup lang="ts">
import Navbar from "../../layout/Navbar.vue";
import AddMeeting from "../BookClub/AddMeeting.vue";
import { ref, onMounted, computed } from "vue";
import BookClubForm from "../BookClub/BookClubForm.vue";
import DiscussionForm from "../BookClub/DiscussionForm.vue";
import { useRoute, useRouter } from "vue-router";
import axios from "axios";
import {
  BOOK_SERVICE_URL,
  BOOKCLUB_IMAGE_SERVER_URL,
  USER_SERVICE_URL,
  AVATAR_SERVER_URL,
} from "../../../config";
import { getProfile } from "../../../composables/useProfile";
import { useAuth } from "../../../composables/useAuth";

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
  is_public?: boolean;
}
interface Meeting {
  id: number;
  title: string;
  date: string;
  status: "upcoming" | "past";
}
interface Member {
  user_id: number;
  role: string;
  username: string;
  avatar_url?: string;
}
interface Discussion {
  id: number;
  title: string;
  content: string;
  user_id: number;
  created_at: string;
  user?: { username: string };
  comment_count: number;
}
interface JoinRequest {
  id: number;
  club_id: number;
  sender_id: number;
  status: string;
  type: string;
  sender_profile?: {
    user_id: number;
    username: string;
    avatar_url?: string;
  };
}

const route = useRoute();
const router = useRouter();
const clubId = Number(route.params.id);
const { userInfo } = useAuth();

const club = ref<Club | null>(null);
const meetings = ref<Meeting[]>([]);
const activeTab = ref("upcoming");
const defaultTab = ref("about");
const showAddMeeting = ref(false);

const showMenu = ref(false);
const showEdit = ref(false);

const searchQuery = ref("");
const searchResults = ref<SearchUser[]>([]);
const isSearching = ref(false);
const inviteMessage = ref("");

const memberCount = ref(0);
const membersList = ref<Member[]>([]);

const discussionsList = ref<Discussion[]>([]);
const showDiscussionForm = ref(false);
const isLoadingDiscussions = ref(false);

const joinRequests = ref<JoinRequest[]>([]);
const isLoadingRequests = ref(false);

const isCreator = computed(() => {
  if (!userInfo.value || !club.value) return false;
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  return userId === club.value.creator_id;
});

const isMember = computed(() => {
  if (!userInfo.value || !membersList.value) return false;
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  return membersList.value.some((member) => member.user_id === userId);
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
    searchResults.value = res.data.filter(
      (user: SearchUser) => user.id !== currentUserId
    );
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
    await axios.post(`${BOOK_SERVICE_URL}bookclubs/${clubId}/invite`, formData);
    inviteMessage.value = "Đã gửi lời mời thành công!";
    searchResults.value = searchResults.value.filter((user) => user.id !== inviteeId);
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
    .filter((line) => line.trim() !== "")
    .map((line) => line.replace(/^\d+\.\s*/, ""));
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
async function getMemberCount(clubId: number) {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${clubId}/member-count`);
    return res.data;
  } catch (error) {
    console.error("Lỗi khi đếm thành viên:", error);
    return { member_count: 0 };
  }
}
async function getMembers(clubId: number) {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${clubId}/members`);
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
    return membersWithProfile;
  } catch (error) {
    console.error("Lỗi khi lấy danh sách thành viên:", error);
    return [];
  }
}
function handleMeetingCreated() {
  showAddMeeting.value = false;
  loadData();
}

async function getDiscussions(clubId: number) {
  isLoadingDiscussions.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${clubId}/discussions`);
    const discussionsWithData = await Promise.all(
      res.data.map(async (discussion: Discussion) => {
        const profile = await getProfile(discussion.user_id);
        return {
          ...discussion,
          user: { username: profile?.username || "Người dùng ẩn" },
          comment_count: discussion.comment_count || 0,
        };
      })
    );
    discussionsList.value = discussionsWithData.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  } catch (error) {
    console.error("Lỗi khi lấy danh sách thảo luận:", error);
  } finally {
    isLoadingDiscussions.value = false;
  }
}

function handleDiscussionCreated() {
  showDiscussionForm.value = false;
  getDiscussions(clubId);
}

async function getJoinRequests(clubId: number) {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!userId) return [];

  isLoadingRequests.value = true;
  try {
    const res = await axios.get(
      `${BOOK_SERVICE_URL}bookclubs/${clubId}/join-requests?user_id=${userId}`
    );

    const requestsWithProfile = await Promise.all(
      res.data.map(async (req: JoinRequest) => {
        const profile = await getProfile(req.sender_id);
        return { ...req, sender_profile: profile };
      })
    );
    return requestsWithProfile;
  } catch (error) {
    console.error("Lỗi khi lấy yêu cầu tham gia:", error);
    return [];
  } finally {
    isLoadingRequests.value = false;
  }
}

async function handleJoinRequest(requestId: number, action: "accept" | "decline") {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!userId) {
    alert("Lỗi xác thực Host");
    return;
  }

  try {
    // Lưu thông tin người gửi trước khi xử lý (để gửi thông báo)
    const requestItem = joinRequests.value.find((r) => r.id === requestId);

    const formData = new FormData();
    formData.append("user_id", String(userId));

    if (action === "accept") {
      await axios.post(
        `${BOOK_SERVICE_URL}bookclubs/request/${requestId}/accept`,
        formData
      );

      // --- THÔNG BÁO CHO NGƯỜI ĐƯỢC DUYỆT ---
      if (requestItem) {
        axios
          .post(`${USER_SERVICE_URL}notifications/add`, {
            receiver_id: requestItem.sender_id,
            sender_id: userId,
            type: "club_join_accepted",
            message: JSON.stringify({
              clubName: club.value?.name || "Câu lạc bộ",
              clubId: clubId,
            }),
            status: "unread",
          })
          .catch((e) => console.error("Lỗi gửi notif duyệt:", e));
      }
      // ----------------------------------------
    } else {
      await axios.delete(`${BOOK_SERVICE_URL}bookclubs/request/${requestId}/decline`, {
        data: formData,
      });
    }

    joinRequests.value = joinRequests.value.filter((req) => req.id !== requestId);
    getMembers(clubId).then((data) => (membersList.value = data));
    getMemberCount(clubId).then((data) => (memberCount.value = data.member_count));
  } catch (err: any) {
    alert(
      `Lỗi khi ${action === "accept" ? "chấp thuận" : "từ chối"}: ${
        err.response?.data?.detail
      }`
    );
  }
}

async function joinClub() {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!userId) {
    alert("Vui lòng đăng nhập để tham gia!");
    return;
  }
  try {
    const formData = new FormData();
    formData.append("user_id", String(userId));
    const res = await axios.post(`${BOOK_SERVICE_URL}bookclubs/${clubId}/join`, formData);

    if (club.value && !club.value.is_public) {
      alert("Đã gửi yêu cầu tham gia. Vui lòng chờ chủ club duyệt.");

      // --- THÔNG BÁO CHO CHỦ CLB ---
      axios
        .post(`${USER_SERVICE_URL}notifications/add`, {
          receiver_id: club.value.creator_id,
          sender_id: userId,
          type: "club_join_request",
          message: JSON.stringify({
            clubName: club.value.name,
            clubId: clubId,
          }),
          status: "unread",
        })
        .catch((e) => console.error("Lỗi gửi notif xin vào:", e));
      // -----------------------------
    } else {
      alert("Tham gia thành công!");
      await Promise.all([getMemberCount(clubId), getMembers(clubId)]).then(
        ([countData, memberData]) => {
          memberCount.value = countData?.member_count || 0;
          membersList.value = memberData || [];
        }
      );
    }
  } catch (err: any) {
    alert(err.response?.data?.detail || "Lỗi khi tham gia");
  }
}

async function leaveClub() {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!userId) {
    alert("Vui lòng đăng nhập!");
    return;
  }
  if (!confirm("Bạn có chắc muốn rời khỏi câu lạc bộ này?")) return;

  try {
    const formData = new FormData();
    formData.append("user_id", String(userId));
    await axios.delete(`${BOOK_SERVICE_URL}bookclubs/${clubId}/leave`, {
      data: formData,
    });

    await Promise.all([getMemberCount(clubId), getMembers(clubId)]).then(
      ([countData, memberData]) => {
        memberCount.value = countData?.member_count || 0;
        membersList.value = memberData || [];
      }
    );
  } catch (err: any) {
    alert(err.response?.data?.detail || "Lỗi khi rời khỏi");
  }
}

async function kickMember(targetUserId: number, targetUsername: string) {
  // Lấy ID người đang đăng nhập
  const currentUserId = userInfo.value?.id || userInfo.value?.user_id;
  
  if (!currentUserId) {
    alert("Lỗi xác thực người dùng.");
    return;
  }

  const confirmMsg = `Bạn có chắc chắn muốn mời thành viên "${targetUsername}" ra khỏi câu lạc bộ?`;
  if (!confirm.call(window, confirmMsg)) return;

  try {
    // Gọi API Backend vừa tạo ở Bước 1
    // Lưu ý: Dùng data: formData để gửi requester_id trong body của DELETE request
    const formData = new FormData();
    formData.append("requester_id", String(currentUserId));

    await axios.delete(`${BOOK_SERVICE_URL}bookclubs/${clubId}/members/${targetUserId}`, {
      data: formData, // Axios delete cần config data thế này để gửi body
      headers: { "Content-Type": "multipart/form-data" }
    });

    alert("Đã xóa thành viên thành công.");

    // Cập nhật lại danh sách thành viên và số lượng ngay lập tức
    membersList.value = membersList.value.filter(m => m.user_id !== targetUserId);
    memberCount.value -= 1;

  } catch (err: any) {
    console.error(err);
    alert(err.response?.data?.detail || "Lỗi khi xóa thành viên.");
  }
}

async function loadData() {
  const clubData = await getClub(clubId);
  if (clubData) {
    const profile = await getProfile(clubData.creator_id);
    club.value = { ...clubData, creator_name: profile.username };
  } else {
    return;
  }

  const [meetingData, memberCountData, memberListData] = await Promise.all([
    getMeetings(clubId),
    getMemberCount(clubId),
    getMembers(clubId),
    getDiscussions(clubId),
  ]);

  if (isCreator.value) {
    joinRequests.value = (await getJoinRequests(clubId)) || [];
  }

  const now = new Date();
  meetings.value = (meetingData || []).map((m: any) => ({
    ...m,
    status: new Date(m.date) > now ? "upcoming" : "past",
  }));
  memberCount.value = memberCountData?.member_count || 0;
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

  <div v-else class="max-w-5xl mx-auto mt-8">
    <BookClubForm
      v-if="showEdit"
      :club-id="clubId"
      @saved="handleEditSaved"
      @cancel="handleEditCancel"
      class="bg-white shadow rounded-xl p-6"
    />

    <div v-else class="bg-white shadow rounded-xl p-6">
      <div class="flex items-start gap-6 border-b pb-4 relative">
        <img
          v-if="club.avatar_url"
          :src="`${BOOKCLUB_IMAGE_SERVER_URL}/${club.avatar_url}`"
          alt="Avatar CLB"
          class="w-24 h-24 object-cover rounded-md border border-gray-300 shadow-sm"
        />
        <div
          v-else
          class="w-24 h-24 bg-gray-200 flex items-center justify-center rounded-md text-gray-500 font-bold text-2xl"
        >
          {{ club.name.charAt(0).toUpperCase() }}
        </div>

        <div class="flex-1">
          <p class="text-sm font-semibold text-yellow-600 uppercase">Câu lạc bộ</p>
          <div class="flex items-center justify-between">
            <h2 class="text-2xl font-bold text-gray-800">{{ club.name }}</h2>

            <div class="relative" v-if="isCreator || isMember">
              <button
                @click="showMenu = !showMenu"
                class="text-gray-500 hover:text-gray-700 text-2xl font-bold px-2"
              >
                ⋮
              </button>

              <div
                v-if="showMenu"
                class="absolute right-0 mt-2 w-32 bg-white border rounded-md shadow-lg z-10"
              >
                <button
                  v-if="isCreator"
                  @click="openEditClub"
                  class="block w-full text-left px-3 py-2 text-sm hover:bg-yellow-50 rounded-md text-gray-700"
                >
                  ✏️ Chỉnh sửa
                </button>

                <button
                  v-if="!isCreator && isMember"
                  @click="leaveClub"
                  class="block w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md"
                >
                  Rời khỏi
                </button>
              </div>
            </div>
          </div>

          <p class="text-gray-600 mt-1">
            Người quản lý:
            <span class="font-semibold text-yellow-600">{{ club.creator_name }}</span>
          </p>
          <p class="text-gray-500 text-sm mt-1">{{ memberCount }} thành viên</p>

          <button
            v-if="!isCreator && !isMember"
            @click="joinClub"
            class="mt-3 px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black text-sm font-semibold rounded-md shadow-sm"
          >
            {{ club.is_public ? "Tham gia câu lạc bộ" : "Gửi yêu cầu tham gia" }}
          </button>
        </div>
      </div>

      <!-- Tabs Navigation -->
      <div v-if="isMember" class="flex flex-wrap space-x-6 mt-4 border-b border-gray-200">
        <button
          v-for="tab in [
            { key: 'upcoming', label: 'Cuộc họp' },
            { key: 'discussions', label: 'Thảo luận' },
            { key: 'members', label: 'Thành viên' },
            { key: 'about', label: 'Giới thiệu' },
            { key: 'rules', label: 'Nội quy' },
          ]"
          :key="tab.key"
          @click="activeTab = tab.key"
          class="py-2 text-sm font-medium transition-colors border-b-2"
          :class="
            activeTab === tab.key
              ? 'text-yellow-600 border-yellow-400'
              : 'text-gray-500 border-transparent hover:text-gray-700'
          "
        >
          {{ tab.label }}
        </button>
      </div>
      <div v-else class="flex flex-wrap space-x-6 mt-4 border-b border-gray-200">
        <button
          v-for="tab in [
            { key: 'about', label: 'Giới thiệu' },
            { key: 'rules', label: 'Nội quy' },
            { key: 'members', label: 'Thành viên' },
          ]"
          :key="tab.key"
          @click="defaultTab = tab.key"
          class="py-2 text-sm font-medium transition-colors border-b-2"
          :class="
            defaultTab === tab.key
              ? 'text-yellow-600 border-yellow-400'
              : 'text-gray-500 border-transparent hover:text-gray-700'
          "
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab Contents -->
      <div v-if="isMember" class="mt-6">
        <div v-if="activeTab === 'upcoming'">
          <div v-if="showAddMeeting">
            <AddMeeting
              :club-id="clubId"
              @created="handleMeetingCreated"
              @cancel="showAddMeeting = false"
            />
          </div>
          <div v-else>
            <div
              v-if="meetings.filter((m) => m.status === 'upcoming').length === 0"
              class="text-center py-10 text-gray-500"
            >
              <p class="font-semibold italic mb-3">Chưa có cuộc họp sắp tới</p>
              <button
                v-if="isCreator"
                @click="showAddMeeting = true"
                class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md transition"
              >
                + Tạo cuộc họp mới
              </button>
            </div>
            <div v-else class="space-y-4">
              <div
                v-for="meeting in meetings.filter((m) => m.status === 'upcoming')"
                :key="meeting.id"
                class="p-4 border rounded-lg flex justify-between items-center hover:bg-gray-50 transition"
              >
                <div>
                  <p class="font-semibold text-gray-800">{{ meeting.title }}</p>
                  <p class="text-sm text-gray-500">
                    Ngày: {{ new Date(meeting.date).toLocaleDateString("vi-VN") }}, Giờ:
                    {{
                      new Date(meeting.date).toLocaleTimeString("vi-VN", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    }}
                  </p>
                </div>
                <button
                  @click="goToMeeting(meeting.id)"
                  class="px-3 py-1 bg-yellow-400 hover:bg-yellow-500 rounded-md text-black text-sm font-medium"
                >
                  Chi tiết
                </button>
              </div>
              <div v-if="isCreator" class="flex justify-center mt-6">
                <button
                  @click="showAddMeeting = true"
                  class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md transition"
                >
                  + Thêm cuộc họp
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'discussions'">
          <div v-if="showDiscussionForm">
            <DiscussionForm
              :club-id="clubId"
              @created="handleDiscussionCreated"
              @cancel="showDiscussionForm = false"
            />
          </div>
          <div v-else>
            <div v-if="isCreator" class="flex justify-end mb-4">
              <button
                @click="showDiscussionForm = true"
                class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md transition"
              >
                + Tạo thảo luận mới
              </button>
            </div>
            <div v-if="isLoadingDiscussions" class="text-center py-10 text-gray-500">
              Đang tải thảo luận...
            </div>
            <div
              v-else-if="discussionsList.length === 0"
              class="text-center py-16 text-gray-500 bg-gray-50 rounded-lg border"
            >
              <span class="text-6xl">💬</span>
              <h3 class="text-xl font-semibold mt-4 text-gray-800">Chưa có thảo luận</h3>
              <p class="mt-1 text-gray-600">
                {{
                  isCreator
                    ? "Hãy tạo một chủ đề để mọi người cùng trao đổi!"
                    : "Chưa có chủ đề nào được tạo."
                }}
              </p>
            </div>
            <div v-else class="space-y-4">
              <router-link
                v-for="post in discussionsList"
                :key="post.id"
                :to="'/discussion/' + post.id"
                class="block p-4 border rounded-lg bg-white shadow-sm hover:shadow-md transition"
              >
                <p class="text-sm text-gray-500">
                  Đăng bởi
                  <span class="font-medium text-gray-700">{{ post.user?.username }}</span
                  ><span class="ml-2"
                    >&bull;
                    {{ new Date(post.created_at).toLocaleDateString("vi-VN") }}</span
                  >
                </p>
                <h3 class="text-lg font-semibold text-gray-800 mt-1">{{ post.title }}</h3>
                <p class="text-gray-600 mt-1 truncate">{{ post.content }}</p>
                <p class="text-sm text-yellow-600 font-medium mt-2">
                  {{ post.comment_count }} bình luận &rarr;
                </p>
              </router-link>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'members'">
          <div v-if="isCreator" class="mb-8 p-4 bg-gray-50 rounded-lg border">
            <h3 class="text-lg font-semibold text-yellow-600 mb-3">Mời thành viên</h3>
            <input
              v-model="searchQuery"
              @input="searchUsers"
              type="text"
              class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
              placeholder="Tìm theo username..."
            />
            <div v-if="isSearching" class="text-gray-500 text-center py-3">
              Đang tìm...
            </div>
            <ul
              v-if="searchResults.length > 0"
              class="mt-4 max-h-60 overflow-y-auto space-y-2"
            >
              <li
                v-for="user in searchResults"
                :key="user.id"
                class="flex justify-between items-center p-2 border rounded-md bg-white hover:bg-gray-100"
              >
                <span class="font-medium text-gray-700">{{ user.username }}</span>
                <button
                  @click="sendInvite(user.id)"
                  class="px-3 py-1 bg-yellow-400 hover:bg-yellow-500 text-black text-sm font-semibold rounded-md"
                >
                  Mời
                </button>
              </li>
            </ul>
            <p v-if="inviteMessage" class="text-sm text-green-600 mt-3">
              {{ inviteMessage }}
            </p>
          </div>

          <div v-if="isCreator && joinRequests.length > 0" class="mb-8">
            <h3 class="text-lg font-semibold text-yellow-600 mb-3">
              Yêu cầu đang chờ duyệt ({{ joinRequests.length }})
            </h3>
            <div class="space-y-3">
              <div
                v-for="req in joinRequests"
                :key="req.id"
                class="flex items-center justify-between p-3 bg-white border rounded-lg shadow-sm"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-700 overflow-hidden shadow-sm"
                  >
                    <img
                      v-if="req.sender_profile?.avatar_url"
                      :src="`${AVATAR_SERVER_URL}/${req.sender_profile.avatar_url}`"
                      class="w-full h-full object-cover rounded-full"
                    />
                    <span v-else class="text-lg">{{
                      req.sender_profile?.username.charAt(0).toUpperCase()
                    }}</span>
                  </div>
                  <span class="font-semibold text-gray-800">{{
                    req.sender_profile?.username
                  }}</span>
                </div>
                <div class="flex gap-2">
                  <button
                    @click="handleJoinRequest(req.id, 'accept')"
                    class="px-3 py-1 bg-yellow-400 hover:bg-yellow-500 text-black text-sm font-semibold rounded-md"
                  >
                    Chấp thuận
                  </button>
                  <button
                    @click="handleJoinRequest(req.id, 'decline')"
                    class="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-semibold rounded-md"
                  >
                    Từ chối
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div>
            <div>
  <h3 class="text-lg font-semibold text-yellow-600 mb-3">Tất cả thành viên ({{ memberCount }})</h3>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    
    <div v-for="member in membersList" :key="member.user_id" 
         class="flex items-center justify-between p-3 bg-white border rounded-lg shadow-sm hover:shadow-md transition-shadow">
      
      <router-link :to="'/profile/' + member.user_id" class="flex items-center gap-3 flex-1">
        <div class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-700 overflow-hidden shadow-sm flex-shrink-0">
          <template v-if="member.avatar_url">
            <img :src="`${AVATAR_SERVER_URL}/${member.avatar_url}`" alt="Avatar" class="w-full h-full object-cover" />
          </template>
          <template v-else>{{ member.username?.charAt(0)?.toUpperCase() || "U" }}</template>
        </div>
        <div>
          <p class="font-semibold text-gray-800 hover:text-yellow-700">{{ member.username }}</p>
          <span v-if="member.role === 'host'" class="text-xs text-yellow-600 font-medium">Người quản lý</span>
          <span v-else class="text-xs text-gray-500">Thành viên</span>
        </div>
      </router-link>

      <button 
        v-if="isCreator && member.role !== 'host'" 
        @click.prevent="kickMember(member.user_id, member.username)"
        class="text-gray-400 hover:text-red-500 p-2 rounded-full hover:bg-red-50 transition-colors"
        title="Mời ra khỏi nhóm"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7a4 4 0 11-8 0 4 4 0 018 0zM9 14a6 6 0 00-6 6v1h12v-1a6 6 0 00-6-6zM21 12h-6" />
        </svg>
      </button>

    </div>
  </div>
</div>
          </div>
        </div>

        <div
          v-else-if="activeTab === 'about' || activeTab === 'rules'"
          class="bg-gray-50 p-4 sm:p-5 rounded-lg border"
        >
          <p
            v-if="activeTab === 'about'"
            class="whitespace-pre-line leading-relaxed text-gray-800"
          >
            {{ club.description || "Chưa có mô tả." }}
          </p>
          <div v-if="activeTab === 'rules' && rulesList.length > 0">
            <ol
              class="list-decimal list-outside pl-5 space-y-2 text-gray-800 leading-relaxed"
            >
              <li v-for="(rule, index) in rulesList" :key="index">{{ rule }}</li>
            </ol>
          </div>
          <p
            v-if="activeTab === 'rules' && rulesList.length === 0"
            class="text-center text-gray-500 italic"
          >
            Chưa có nội quy.
          </p>
        </div>
      </div>

      <!-- Non-member View -->
      <div v-else class="mt-6">
        <div
          v-if="defaultTab === 'about' || defaultTab === 'rules'"
          class="bg-gray-50 p-4 sm:p-5 rounded-lg border"
        >
          <p
            v-if="defaultTab === 'about'"
            class="whitespace-pre-line leading-relaxed text-gray-800"
          >
            {{ club.description || "Chưa có mô tả." }}
          </p>
          <div v-if="defaultTab === 'rules' && rulesList.length > 0">
            <ol
              class="list-decimal list-outside pl-5 space-y-2 text-gray-800 leading-relaxed"
            >
              <li v-for="(rule, index) in rulesList" :key="index">{{ rule }}</li>
            </ol>
          </div>
          <p
            v-if="defaultTab === 'rules' && rulesList.length === 0"
            class="text-center text-gray-500 italic"
          >
            Chưa có nội quy.
          </p>
        </div>
        <div v-else-if="defaultTab === 'members'">
          <h3 class="text-lg font-semibold text-yellow-600 mb-3">
            Tất cả thành viên ({{ memberCount }})
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <router-link
              v-for="member in membersList"
              :key="member.user_id"
              :to="'/profile/' + member.user_id"
              class="flex items-center gap-3 p-3 bg-white border rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
            >
              <div
                class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-700 overflow-hidden shadow-sm flex-shrink-0"
              >
                <template v-if="member.avatar_url"
                  ><img
                    :src="`${AVATAR_SERVER_URL}/${member.avatar_url}`"
                    alt="Avatar"
                    class="w-full h-full object-cover"
                /></template>
                <template v-else>{{
                  member.username?.charAt(0)?.toUpperCase() || "U"
                }}</template>
              </div>
              <div>
                <p class="font-semibold text-gray-800 hover:text-yellow-700">
                  {{ member.username }}
                </p>
                <span
                  v-if="member.role === 'host'"
                  class="text-xs text-yellow-600 font-medium"
                  >Người quản lý</span
                >
                <span v-else class="text-xs text-gray-500">Thành viên</span>
              </div>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
