<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import axios from 'axios';
import { useAuth } from '../../composables/useAuth';
import { getProfile } from '../../composables/useProfile';
import { BOOK_SERVICE_URL, AVATAR_SERVER_URL } from '../../config';

const props = defineProps<{
    bookId: number | string;
    bookTitle: string; 
}>();

const { userInfo } = useAuth();

// --- STATE QUẢN LÝ PHÂN TRANG & SORT ---
const quotes = ref<any[]>([]);
const loading = ref(false);
const sortBy = ref<'top' | 'newest'>('top'); // Mặc định là Hay nhất
const page = ref(1);
const hasMore = ref(true); // Còn dữ liệu để load ko?
const limit = 5; // Mỗi lần load 5 cái

const showForm = ref(false);
const newQuoteText = ref("");
const isSubmitting = ref(false);
const submitSuccess = ref(false);
const copyFeedback = ref<number | null>(null);

onMounted(() => {
    fetchQuotes(true); // true = reset list (load trang 1)
});

// Watch khi đổi tab sort -> Reset và load lại từ đầu
watch(sortBy, () => {
    fetchQuotes(true);
});

// Hàm fetch dữ liệu
async function fetchQuotes(reset = false) {
    if (loading.value) return;
    
    loading.value = true;
    
    if (reset) {
        page.value = 1;
        quotes.value = [];
        hasMore.value = true;
    }

    try {
        const params = {
            current_user_id: userInfo.value?.user_id,
            page: page.value,
            limit: limit,
            sort_by: sortBy.value
        };
        
        const res = await axios.get(`${BOOK_SERVICE_URL}books/${props.bookId}/quotes`, { params });
        
        // Xử lý Profile song song
        const newQuotes = await Promise.all(res.data.map(async (q: any) => {
            const userProfile = await getProfile(q.user_id);
            return {
                id: q.id,
                text: q.content,
                user_id: q.user_id,
                user_name: userProfile?.full_name || userProfile?.username || q.user_name,
                user_avatar: userProfile?.avatar_url || null,
                likes: q.like_count,
                is_liked: q.is_liked,
                created_at: new Date(q.created_at).toLocaleDateString('vi-VN'),
                tags: [] 
            };
        }));

        if (newQuotes.length < limit) {
            hasMore.value = false; // Đã hết dữ liệu
        }

        quotes.value.push(...newQuotes); // Nối thêm vào danh sách cũ
        page.value++; // Tăng trang cho lần sau

    } catch (e) {
        console.error("Lỗi tải quotes:", e);
    } finally {
        loading.value = false;
    }
}

async function handleLike(quote: any) {
    if (!userInfo.value) return alert("Vui lòng đăng nhập!");
    const previousLiked = quote.is_liked;
    
    // Optimistic UI
    quote.is_liked = !quote.is_liked;
    quote.likes += quote.is_liked ? 1 : -1;

    try {
        await axios.post(`${BOOK_SERVICE_URL}quotes/${quote.id}/like`, {
            current_user_id: userInfo.value.user_id
        });
    } catch (e) {
        quote.is_liked = previousLiked;
        quote.likes += quote.is_liked ? 1 : -1;
    }
}

async function handleSubmit() {
    if (!newQuoteText.value.trim()) return;
    isSubmitting.value = true;
    try {
        const payload = {
            request: { book_id: props.bookId, content: newQuoteText.value },
            current_user_id: userInfo.value.user_id
        };
        const res = await axios.post(`${BOOK_SERVICE_URL}quotes`, payload);
        
        // Khi đăng xong, thêm vào đầu list và reset về tab "Mới nhất" để user thấy bài mình
        const myProfile = await getProfile(userInfo.value.user_id);
        const newQuote = {
            id: res.data.id,
            text: res.data.content,
            user_id: userInfo.value.user_id,
            user_name: myProfile?.full_name || userInfo.value.username,
            user_avatar: myProfile?.avatar_url || null,
            likes: 0, is_liked: false, created_at: 'Vừa xong', tags: []
        };
        
        // Nếu đang ở tab Top, bài mới 0 like sẽ chìm nghỉm, nên ta chuyển tab
        if (sortBy.value === 'top') {
            sortBy.value = 'newest'; // Tự động trigger watch -> reload list
        } else {
            quotes.value.unshift(newQuote);
        }

        newQuoteText.value = "";
        showForm.value = false;
        submitSuccess.value = true;
        setTimeout(() => submitSuccess.value = false, 3000);
    } catch (e) { alert("Lỗi đăng bài"); } 
    finally { isSubmitting.value = false; }
}

function handleCopy(quote: any) {
    const textToCopy = `"${quote.text}"\n— Sách: ${props.bookTitle}`;
    navigator.clipboard.writeText(textToCopy);
    copyFeedback.value = quote.id;
    setTimeout(() => copyFeedback.value = null, 2000);
}
</script>

<template>
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <!-- Header + Tabs -->
        <div class="p-6 border-b border-gray-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h3 class="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <span class="text-yellow-500 text-2xl font-serif">❝</span>
                    Trích dẫn nổi bật
                </h3>
                
                <!-- TABS SORTING -->
                <div class="flex gap-4 mt-2 text-sm font-medium">
                    <button 
                        @click="sortBy = 'top'"
                        class="pb-1 transition-colors relative"
                        :class="sortBy === 'top' ? 'text-yellow-600' : 'text-gray-400 hover:text-gray-600'"
                    >
                        🔥 Hay nhất
                        <span v-if="sortBy === 'top'" class="absolute bottom-0 left-0 w-full h-0.5 bg-yellow-500"></span>
                    </button>
                    <button 
                        @click="sortBy = 'newest'"
                        class="pb-1 transition-colors relative"
                        :class="sortBy === 'newest' ? 'text-yellow-600' : 'text-gray-400 hover:text-gray-600'"
                    >
                        ✨ Mới nhất
                        <span v-if="sortBy === 'newest'" class="absolute bottom-0 left-0 w-full h-0.5 bg-yellow-500"></span>
                    </button>
                </div>
            </div>
            
            <button v-if="userInfo && !showForm" @click="showForm = true"
                class="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition shadow-md hover:shadow-lg active:scale-95">
                <span>✚</span> Viết trích dẫn
            </button>
        </div>

        <!-- Form (Giữ nguyên) -->
        <transition name="slide-fade">
            <div v-if="showForm" class="p-6 bg-gray-50 border-b border-gray-100">
                <textarea v-model="newQuoteText" rows="3"
                    class="w-full p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none text-gray-700 text-sm bg-white shadow-inner resize-none"
                    placeholder="Nhập nội dung trích dẫn chính xác..."></textarea>
                <div class="flex justify-end gap-3 mt-3">
                    <button @click="showForm = false" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 font-medium">Hủy</button>
                    <button @click="handleSubmit" :disabled="!newQuoteText.trim() || isSubmitting"
                        class="px-5 py-2 bg-yellow-500 text-white text-sm font-bold rounded-lg hover:bg-yellow-600 transition disabled:opacity-50 flex items-center gap-2">
                        <span v-if="isSubmitting" class="animate-spin">⏳</span> {{ isSubmitting ? 'Đang đăng...' : 'Đăng ngay' }}
                    </button>
                </div>
            </div>
        </transition>

        <div v-if="submitSuccess" class="bg-green-50 text-green-700 p-3 text-sm text-center font-medium">✅ Đã đăng thành công!</div>

        <!-- Content -->
        <div class="p-6">
            <!-- Empty State -->
            <div v-if="quotes.length === 0 && !loading" class="text-center py-10">
                <div class="text-4xl mb-3">🍃</div>
                <p class="text-gray-500 font-medium">Chưa có trích dẫn nào.</p>
            </div>

            <!-- List -->
            <div class="space-y-8">
                <div v-for="quote in quotes" :key="quote.id" class="group relative pl-6 border-l-4 border-gray-200 hover:border-yellow-400 transition-colors duration-300">
                    <div class="relative z-10 mt-2 pr-6">
                        <span class="text-4xl text-gray-300 group-hover:text-yellow-400 font-serif pointer-events-none select-none transition-colors duration-300 opacity-60 leading-none mr-2 relative top-2">“</span>
                        <p class="text-lg text-gray-800 font-serif italic leading-relaxed mb-3 inline">{{ quote.text }}</p>
                        <span class="text-4xl text-gray-300 group-hover:text-yellow-400 font-serif pointer-events-none select-none transition-colors duration-300 opacity-60 leading-none ml-1 relative top-2">”</span>

                        <div class="flex items-center justify-between border-t border-gray-100 pt-3 mt-3">
                            <div class="flex items-center gap-2">
                                <img v-if="quote.user_avatar" :src="`${AVATAR_SERVER_URL}/${quote.user_avatar}`" class="w-8 h-8 rounded-full border border-gray-200 object-cover">
                                <div v-else class="w-8 h-8 rounded-full bg-gradient-to-r from-blue-400 to-indigo-500 flex items-center justify-center text-xs text-white font-bold border border-gray-200">
                                    {{ quote.user_name?.charAt(0).toUpperCase() || 'U' }}
                                </div>
                                <span class="text-xs text-gray-500 font-medium">{{ quote.user_name }}</span>
                                <span class="text-gray-300 text-xs">•</span>
                                <span class="text-xs text-gray-400">{{ quote.created_at }}</span>
                            </div>
                            <div class="flex items-center gap-4">
                                <div class="flex items-center gap-1 bg-gray-50 rounded-full px-2 py-1">
                                    <button @click="handleLike(quote)" class="flex items-center gap-1 px-2 py-1 rounded-full transition-all active:scale-95" :class="quote.is_liked ? 'text-red-500 bg-red-50' : 'text-gray-400 hover:text-gray-600'">
                                        <span class="text-lg">{{ quote.is_liked ? '❤️' : '♡' }}</span>
                                        <span class="text-xs font-bold">{{ quote.likes }}</span>
                                    </button>
                                    <div class="w-px h-4 bg-gray-200"></div>
                                    <button @click="handleCopy(quote)" class="relative px-2 py-1 text-gray-400 hover:text-blue-500 transition" title="Sao chép">
                                        <span v-if="copyFeedback === quote.id" class="absolute -top-8 left-1/2 -translate-x-1/2 bg-black text-white text-[10px] px-2 py-1 rounded shadow-lg whitespace-nowrap">Đã chép!</span>
                                        📄
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Loading & Load More -->
            <div class="mt-8 text-center">
                <div v-if="loading" class="flex justify-center gap-1">
                    <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                    <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></span>
                    <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
                </div>
                
                <button 
                    v-else-if="hasMore" 
                    @click="fetchQuotes(false)" 
                    class="text-sm text-gray-500 hover:text-yellow-600 font-medium underline decoration-dotted underline-offset-4"
                >
                    Xem thêm trích dẫn cũ hơn
                </button>
                
                <div v-else-if="quotes.length > 0" class="text-xs text-gray-400 italic">
                    Đã hiển thị hết trích dẫn.
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.slide-fade-enter-active { transition: all 0.3s ease-out; }
.slide-fade-leave-active { transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1); }
.slide-fade-enter-from, .slide-fade-leave-to { transform: translateY(-10px); opacity: 0; }
</style>