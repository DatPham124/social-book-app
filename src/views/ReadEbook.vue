<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { BOOK_SERVICE_URL, EBOOK_SERVER_URL } from '../config'; 
import { useAuth } from '../composables/useAuth';

// Import Components
import EpubReader from '../components/books/EpubReader.vue';
// KHÔNG CẦN IMPORT VuePdfEmbed NỮA

const route = useRoute();
const router = useRouter();
const bookId = Number(route.params.id);

// --- STATE ---
const bookUrl = ref<string | null>(null);
const bookFormat = ref<'epub' | 'pdf' | null>(null);
const bookTitle = ref("");
const loading = ref(true);
const error = ref("");

// --- LOGIC TẢI SÁCH ---
async function loadBook() {
    loading.value = true;
    try {
        const res = await axios.get(`${BOOK_SERVICE_URL}books/${bookId}`);
        bookTitle.value = res.data.title;
        
        const filename = res.data.file_url || res.data.epub_file; 

        if (filename) {
            if (filename.startsWith('http')) {
                bookUrl.value = filename;
            } else {
                const safeFilename = encodeURIComponent(filename).replace(/%2F/g, "/");
                bookUrl.value = `${EBOOK_SERVER_URL}/${safeFilename}`;
            }
        }

        // Xác định định dạng
        if (bookUrl.value) {
            const cleanUrl = bookUrl.value.split('?')[0].toLowerCase();
            if (cleanUrl.endsWith('.epub')) {
                bookFormat.value = 'epub';
            } else {
                bookFormat.value = 'pdf'; 
            }
        }
    } catch (e) {
        console.error(e);
        error.value = "Không thể tải sách.";
    } finally {
        loading.value = false;
    }
}

onMounted(() => {
    loadBook();
});
</script>

<template>
    <div class="h-screen w-screen bg-gray-100 overflow-hidden flex flex-col">
        
        <!-- LOADING -->
        <div v-if="loading" class="flex-1 flex items-center justify-center">
            <span class="text-gray-500 font-medium">Đang tải sách...</span>
        </div>

        <!-- ERROR -->
        <div v-else-if="error" class="flex-1 flex flex-col items-center justify-center text-red-500 gap-4">
            <p>{{ error }}</p>
            <button @click="router.back()" class="px-4 py-2 bg-white border rounded shadow">Quay lại</button>
        </div>

        <!-- 1. TRÌNH ĐỌC EPUB (Vẫn giữ nguyên vì trình duyệt không đọc được EPUB) -->
        <EpubReader 
            v-else-if="bookFormat === 'epub' && bookUrl" 
            :url="bookUrl" 
            @close="router.back()"
        />

        <!-- 2. TRÌNH ĐỌC PDF (NATIVE BROWSER VIEWER) -->
        <div v-else-if="bookFormat === 'pdf' && bookUrl" class="flex flex-col h-full w-full relative">
            
            <!-- Nút thoát đè lên trên góc -->
            <button 
                @click="router.back()" 
                class="absolute top-4 left-4 z-50 bg-gray-800 text-white px-4 py-2 rounded shadow-lg hover:bg-black transition-colors opacity-50 hover:opacity-100 flex items-center gap-2"
            >
                <span>✕</span> Thoát
            </button>

            <!-- IFRAME NHÚNG PDF -->
            <!-- Trình duyệt sẽ tự render giao diện PDF đầy đủ tính năng ở đây -->
            <iframe 
                :src="bookUrl" 
                class="w-full h-full border-none"
                allow="fullscreen"
            ></iframe>

        </div>

    </div>
</template>