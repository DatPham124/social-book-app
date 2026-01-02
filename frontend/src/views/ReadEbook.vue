<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { jwtDecode } from "jwt-decode"; 
import { BOOK_SERVICE_URL, EBOOK_SERVER_URL } from '../config'; 
import EpubReader from '../components/books/EpubReader.vue';

const route = useRoute();
const router = useRouter();
const bookId = Number(route.params.id);

// --- STATE ---
const bookUrl = ref<string | null>(null);
const bookFormat = ref<'epub' | 'pdf' | null>(null);
const bookTitle = ref("");
const bookPageCount = ref<number>(0); // <--- THÊM BIẾN NÀY
const loading = ref(true);
const error = ref("");

const savedLocation = ref<string | undefined>(undefined);
const currentUserId = ref<number | undefined>(undefined);

const token = localStorage.getItem("token");
if (token) {
    try {
        const decoded: any = jwtDecode(token);
        currentUserId.value = decoded.user_id || decoded.id;
    } catch (e) {
        console.error("Token lỗi", e);
    }
}

async function loadReadingProgress() {
    if (currentUserId.value === undefined) return;
    try {
        const res = await axios.get(
            `${BOOK_SERVICE_URL}books/reading-progress/${currentUserId.value}/${bookId}`
        );
        if (res.data && res.data.current_cfi) {
            savedLocation.value = res.data.current_cfi;
        }
    } catch (e) {
        console.log("Chưa có tiến độ đọc");
    }
}

async function loadBook() {
    loading.value = true;
    try {
        await Promise.all([
            (async () => {
                const res = await axios.get(`${BOOK_SERVICE_URL}books/${bookId}`);
                bookTitle.value = res.data.title;
                bookPageCount.value = res.data.page_count || 0; // <--- LẤY SỐ TRANG CỨNG
                
                const filename = res.data.file_url || res.data.epub_file; 
                if (filename) {
                    if (filename.startsWith('http')) {
                        bookUrl.value = filename;
                    } else {
                        const safeFilename = encodeURIComponent(filename).replace(/%2F/g, "/");
                        bookUrl.value = `${EBOOK_SERVER_URL}/${safeFilename}`;
                    }
                }
                
                if (bookUrl.value) {
                    const cleanUrl = bookUrl.value.split('?')[0].toLowerCase();
                    if (cleanUrl.endsWith('.epub')) {
                        bookFormat.value = 'epub';
                    } else {
                        bookFormat.value = 'pdf'; 
                    }
                }
            })(),
            loadReadingProgress()
        ]);
        
    } catch (e) {
        console.error(e);
        error.value = "Không thể tải sách.";
    } finally {
        loading.value = false;
    }
}

const handleCloseBook = () => {
    if (window.history.state && window.history.state.back) {
        router.back();
    } else {
        router.push("/"); 
    }
};

onMounted(() => {
    loadBook();
});
</script>

<template>
    <div class="h-screen w-screen bg-gray-100 overflow-hidden flex flex-col">
        
        <div v-if="loading" class="flex-1 flex items-center justify-center">
            <span class="text-gray-500 font-medium">Đang tải sách...</span>
        </div>

        <div v-else-if="error" class="flex-1 flex flex-col items-center justify-center text-red-500 gap-4">
            <p>{{ error }}</p>
            <button @click="router.back()" class="px-4 py-2 bg-white border rounded shadow">Quay lại</button>
        </div>

        <!-- TRUYỀN THÊM bookPageCount VÀO CON -->
        <EpubReader 
            v-else-if="bookFormat === 'epub' && bookUrl" 
            :url="bookUrl"
            :bookId="bookId"
            :userId="currentUserId"
            :initialLocation="savedLocation"
            :bookPageCount="bookPageCount"
            @close="handleCloseBook"
        />

        <div v-else-if="bookFormat === 'pdf' && bookUrl" class="flex flex-col h-full w-full relative">
            <button 
                @click="handleCloseBook" 
                class="absolute top-4 left-4 z-50 bg-gray-800 text-white px-4 py-2 rounded shadow-lg hover:bg-black transition-colors opacity-50 hover:opacity-100 flex items-center gap-2"
            >
                <span>✕</span> Thoát
            </button>
            <iframe :src="bookUrl" class="w-full h-full border-none" allow="fullscreen"></iframe>
        </div>

    </div>
</template>