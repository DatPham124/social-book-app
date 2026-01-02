import { ref, computed, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import { USER_SERVICE_URL, BOOK_SERVICE_URL } from '../config';
import { useAuth } from './useAuth';
import { getProfile } from './useProfile';

const notifications = ref<any[]>([]);
const loading = ref(false);
let pollingInterval: any = null;

// HÀM MỚI: Xử lý múi giờ UTC -> Local
function parseUtcTime(dateString: string) {
    if (!dateString) return Date.now();
    // Nếu chuỗi chưa có 'Z' (chỉ báo UTC), hãy thêm vào
    if (typeof dateString === 'string' && !dateString.endsWith('Z')) {
        return new Date(dateString + 'Z').getTime();
    }
    return new Date(dateString).getTime();
}

export function useNotifications() {
    const { userInfo } = useAuth();

    const unreadCount = computed(() => {
        return notifications.value.filter(n => {
            if (n.category === 'normal') return n.status === 'unread';
            if (n.category === 'invite') return n.status === 'pending';
            return false;
        }).length;
    });

    const fetchNotifications = async () => {
        if (!userInfo.value) return;
        
        try {
            const userId = userInfo.value.user_id;
            // Gọi 3 API song song: Thông báo thường, Lời mời Đọc chung, Lời mời CLB
            const [notifRes, buddyRes, clubRes] = await Promise.all([
                axios.get(`${USER_SERVICE_URL}notifications/user/${userId}`),
                axios.get(`${BOOK_SERVICE_URL}buddyreads/invitations/${userId}`),
                axios.get(`${BOOK_SERVICE_URL}bookclubs/invitations/${userId}`)
            ]);

            // 1. XỬ LÝ THÔNG BÁO THƯỜNG (Từ User Service)
            const rawNormalNotifs = await Promise.all(notifRes.data.map(async (item: any) => {
                const sender = await getProfile(item.sender_id);
                
                let displayMsg = item.message;
                let roomId = null;
                
                // --- LOGIC PARSE CÁC LOẠI THÔNG BÁO ---
                if (item.type === 'buddy_chat') {
                    try {
                        // Kiểm tra nếu message là JSON string
                        if (item.message.startsWith('{')) {
                            const parsed = JSON.parse(item.message);
                            displayMsg = parsed.text || item.message;
                            roomId = parsed.roomId;
                        }
                    } catch {
                        displayMsg = item.message;
                    }
                } 
                else if (item.type === 'buddy_comment') {
                     displayMsg = item.message;
                }
                // --- [MỚI] XỬ LÝ THÔNG BÁO KẾT BẠN ---
                else if (item.type === 'friend_request') {
                    displayMsg = "đã gửi lời mời kết bạn";
                }
                // --------------------------------------
                
                // --- CÁC LOẠI THÔNG BÁO CLB ---
                else if (item.type === 'club_meeting') {
                    try {
                        const parsed = JSON.parse(item.message);
                        displayMsg = `đã tạo cuộc họp "${parsed.title}" trong CLB ${parsed.clubName}`;
                        roomId = `meeting_${parsed.meetingId}`;
                    } catch { displayMsg = item.message; }
                }
                else if (item.type === 'club_discussion') {
                    try {
                        const parsed = JSON.parse(item.message);
                        displayMsg = `đã tạo thảo luận "${parsed.title}" trong CLB ${parsed.clubName}`;
                        roomId = `discussion_${parsed.discussionId}`;
                    } catch { displayMsg = item.message; }
                }
                else if (item.type === 'club_comment') {
                    try {
                        const parsed = JSON.parse(item.message);
                        displayMsg = `đã bình luận trong bài "${parsed.discussionTitle}": "${parsed.content}"`;
                        roomId = `discussion_${parsed.discussionId}`;
                    } catch { displayMsg = item.message; }
                }
                else if (item.type === 'club_join_request') {
                    try {
                        const parsed = JSON.parse(item.message);
                        displayMsg = `muốn tham gia câu lạc bộ "${parsed.clubName}"`;
                        roomId = `club_members_${parsed.clubId}`;
                    } catch { displayMsg = item.message; }
                }
                else if (item.type === 'club_join_accepted') {
                    try {
                        const parsed = JSON.parse(item.message);
                        displayMsg = `đã duyệt yêu cầu tham gia CLB "${parsed.clubName}"`;
                        roomId = `club_${parsed.clubId}`;
                    } catch { displayMsg = item.message; }
                }
                else if (item.type === 'quote_like') {
                    try {
                        const parsed = JSON.parse(item.message);
                        displayMsg = `đã thích trích dẫn của bạn trong sách "${parsed.bookTitle}": "${parsed.quoteContent}"`;
                    } catch { 
                        displayMsg = "đã thích trích dẫn của bạn"; 
                    }
                }

                else if (item.type === 'book_recommendation') {
                    try {
                        const parsed = JSON.parse(item.message);
                        const note = parsed.note ? `: "${parsed.note}"` : '';
                        displayMsg = `đã giới thiệu cuốn sách "${parsed.bookTitle}"${note}`;
                        
                        roomId = `book_${parsed.bookId}`; 
                    } catch { 
                        displayMsg = "đã giới thiệu một cuốn sách cho bạn"; 
                    }
                }

                return {
                    ...item,
                    category: 'normal',
                    sender_info: sender,
                    display_message: displayMsg,
                    room_id: roomId,
                    timestamp: parseUtcTime(item.created_at)
                };
            }));

            // --- GOM NHÓM TIN NHẮN CHAT (Grouping) ---
            const processedNotifs: any[] = [];
            const chatGroups: { [key: string]: any } = {};

            rawNormalNotifs.forEach(notif => {
                if (notif.type === 'buddy_chat' && notif.status === 'unread') {
                    const key = notif.room_id || 'unknown';
                    if (!chatGroups[key]) {
                        chatGroups[key] = {
                            ...notif,
                            count: 1,
                            display_message: "đã gửi tin nhắn trong nhóm", 
                            ids_to_read: [notif.id]
                        };
                        processedNotifs.push(chatGroups[key]);
                    } else {
                        chatGroups[key].count++;
                        chatGroups[key].timestamp = Math.max(chatGroups[key].timestamp, notif.timestamp);
                        chatGroups[key].ids_to_read.push(notif.id);
                        chatGroups[key].display_message = `và ${chatGroups[key].count - 1} người khác đã nhắn tin`;
                    }
                } else {
                    processedNotifs.push(notif);
                }
            });

            // 2. XỬ LÝ LỜI MỜI ĐỌC CHUNG (Buddy Read)
            const buddyInvites = await Promise.all(buddyRes.data.map(async (item: any) => {
                const sender = await getProfile(item.sender_id);
                let bookTitle = "sách";
                try {
                    const brRes = await axios.get(`${BOOK_SERVICE_URL}buddyreads/${item.buddy_read_id}`);
                    const bRes = await axios.get(`${BOOK_SERVICE_URL}books/${brRes.data.book_id}`);
                    bookTitle = bRes.data.title;
                } catch (err) { }

                return {
                    ...item,
                    type: 'buddy_read_invite',
                    category: 'invite',
                    status: item.status,
                    sender_info: sender,
                    book_title: bookTitle,
                    display_message: `mời bạn đọc chung cuốn "${bookTitle}"`,
                    timestamp: parseUtcTime(item.created_at)
                };
            }));

            // 3. XỬ LÝ LỜI MỜI CLB (Book Club)
            const clubInvites = await Promise.all(clubRes.data.map(async (item: any) => {
                const sender = await getProfile(item.sender_id);
                let clubName = "Câu lạc bộ";
                try {
                    const cRes = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${item.club_id}`);
                    clubName = cRes.data.name;
                } catch {}

                return {
                    ...item,
                    type: 'bookclub_invite',
                    category: 'invite',
                    status: item.status,
                    sender_info: sender,
                    club_name: clubName,
                    display_message: `đã mời bạn tham gia CLB "${clubName}"`,
                    timestamp: parseUtcTime(item.created_at)
                };
            }));

            const merged = [...processedNotifs, ...buddyInvites, ...clubInvites];
            merged.sort((a, b) => b.timestamp - a.timestamp);
            notifications.value = merged;

        } catch (e) { console.error(e); } finally { loading.value = false; }
    };

    const markAsRead = async (item: any) => {
        try {
            if (item.type === 'buddy_chat' && item.ids_to_read) {
                await Promise.all(item.ids_to_read.map((id: number) => 
                    axios.put(`${USER_SERVICE_URL}notifications/${id}/read`)
                ));
            } else {
                await axios.put(`${USER_SERVICE_URL}notifications/${item.id}/read`);
            }
            fetchNotifications();
        } catch (e) { console.error(e); }
    };

    const handleBuddyInvite = async (item: any, action: 'accept' | 'decline') => {
        try {
            const endpoint = `${BOOK_SERVICE_URL}buddyreads/invitations/${item.id}`;
            if (action === 'accept') await axios.post(`${endpoint}/accept`);
            else await axios.delete(`${endpoint}/decline`);
            fetchNotifications(); 
        } catch (e) { alert("Lỗi xử lý"); }
    };

    // [MỚI] Hàm xử lý lời mời CLB
    const handleClubInvite = async (item: any, action: 'accept' | 'decline') => {
        try {
            const endpoint = `${BOOK_SERVICE_URL}bookclubs/invitations/${item.id}`;
            if (action === 'accept') await axios.post(`${endpoint}/accept`);
            else await axios.delete(`${endpoint}/decline`);
            fetchNotifications();
        } catch (e) { alert("Lỗi xử lý"); }
    };

    const startPolling = () => {
        fetchNotifications();
        if (!pollingInterval) pollingInterval = setInterval(fetchNotifications, 15000);
    };
    const stopPolling = () => {
        if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null; }
    };

    return {
        notifications, unreadCount, loading,
        fetchNotifications, markAsRead, 
        handleBuddyInvite, handleClubInvite, // Export thêm hàm này
        startPolling, stopPolling
    };
}