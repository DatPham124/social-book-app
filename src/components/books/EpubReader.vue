<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import ePub, { Book, Rendition } from 'epubjs';

// Định nghĩa Props & Emits
const props = defineProps<{
    url: string;
    initialLocation?: string; 
}>();

const emit = defineEmits(['close', 'location-change']);

// --- STATE ---
const book = ref<Book | null>(null);
const rendition = ref<Rendition | null>(null);

const isReady = ref(false);
// const showMenu = ref(true); // Đã bỏ biến showMenu để thanh luôn hiện
const showTOC = ref(false); 
const showSettings = ref(false); 
const isFullscreen = ref(false); // State fullscreen

// Dữ liệu sách
const toc = ref<any[]>([]);
const progress = ref(0);

// --- SETTINGS STATE ---
// Chế độ xem: 'single' (1 trang), 'double' (2 trang), 'scroll' (cuộn)
const viewMode = ref<'single' | 'double' | 'scroll'>('single');

// Font & Text
const fontSize = ref(100); // %
const fontName = ref('Helvetica, Arial, sans-serif');
const lineHeight = ref(1.5); 

// Colors
const backgroundColor = ref('#ffffff');
const textColor = ref('#000000');
const brightness = ref(100); // % độ sáng

// Danh sách Font mẫu
const fontOptions = [
    { label: 'Mặc định', value: 'Helvetica, Arial, sans-serif' },
    { label: 'Times New Roman', value: '"Times New Roman", serif' },
    { label: 'Arial', value: 'Arial, sans-serif' },
    { label: 'Verdana', value: 'Verdana, sans-serif' },
    { label: 'Georgia', value: 'Georgia, serif' },
];

// Danh sách Line Height
const lineHeightOptions = [1.0, 1.25, 1.5, 1.75, 2.0];

// Element Refs
const viewerRef = ref<HTMLElement | null>(null);

// --- LOGIC LĂN CHUỘT (WHEEL) ---
let wheelTimeout: any = null; // Dùng để chặn lật trang liên tục quá nhanh

const handleWheel = (e: WheelEvent) => {
    // Nếu đang ở chế độ cuộn (scroll view) thì để trình duyệt tự cuộn, không can thiệp
    if (viewMode.value === 'scroll') return;

    // Debounce: Chặn sự kiện nếu vừa mới lật trang
    if (wheelTimeout) return;

    if (e.deltaY > 0) {
        // Lăn xuống -> Trang sau
        nextPage();
        wheelTimeout = setTimeout(() => wheelTimeout = null, 400); // Chờ 400ms mới được lật tiếp
    } else if (e.deltaY < 0) {
        // Lăn lên -> Trang trước
        prevPage();
        wheelTimeout = setTimeout(() => wheelTimeout = null, 400);
    }
};

// --- KHỞI TẠO EPUB ---
onMounted(() => {
    if (!props.url || !viewerRef.value) return;

    book.value = ePub(props.url);

    rendition.value = book.value.renderTo(viewerRef.value as any, {
        width: '100%',
        height: '100%',
        flow: 'paginated', 
        manager: 'default',
    });

    const displayPromise = props.initialLocation 
        ? rendition.value.display(props.initialLocation)
        : rendition.value.display();

    displayPromise.then(() => {
        isReady.value = true;
        applySettings(); 
        updateViewMode(); 
    });

    // Hook vào nội dung sách để bắt sự kiện lăn chuột và phím bấm bên trong iframe
    rendition.value.hooks.content.register((contents: any) => {
        const doc = contents.window.document;
        const win = contents.window;

        // Bắt lăn chuột
        win.addEventListener('wheel', handleWheel);
        
        // Bắt phím bấm (để phím mũi tên hoạt động khi focus vào sách)
        win.addEventListener('keydown', handleKeydown);

        // Đã bỏ sự kiện click để ẩn/hiện menu
        doc.addEventListener('click', () => {
             // Không làm gì hoặc đóng các popup phụ
             if (showSettings.value) showSettings.value = false;
             if (showTOC.value) showTOC.value = false;
        });
    });

    book.value.loaded.navigation.then((nav: any) => {
        toc.value = nav.toc;
    });

    rendition.value.on('relocated', (location: any) => {
        progress.value = location.start.percentage;
        emit('location-change', location.start.cfi);
    });

    // Đã bỏ logic ẩn/hiện menu khi click vùng viền
    rendition.value.on('click', () => {
        if (showSettings.value) showSettings.value = false;
        if (showTOC.value) showTOC.value = false;
    });

    window.addEventListener('keydown', handleKeydown);
    window.addEventListener('wheel', handleWheel); // Bắt lăn chuột ở vùng ngoài iframe
    document.addEventListener('fullscreenchange', checkFullscreen);
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
    window.removeEventListener('wheel', handleWheel);
    document.removeEventListener('fullscreenchange', checkFullscreen);
    if (book.value) {
        book.value.destroy();
    }
});

// --- LOGIC ĐIỀU KHIỂN ---

const prevPage = () => rendition.value?.prev();
const nextPage = () => rendition.value?.next();

const handleKeydown = (e: KeyboardEvent) => {
    if (e.key === 'ArrowLeft') prevPage();
    if (e.key === 'ArrowRight') nextPage();
};

const goToChapter = (href: string) => {
    rendition.value?.display(href);
    showTOC.value = false;
    // showMenu.value = false; // Menu luôn hiện
};

// Fullscreen Logic
const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
};

const checkFullscreen = () => {
    isFullscreen.value = !!document.fullscreenElement;
};

// --- LOGIC SETTINGS ---

const applySettings = () => {
    if (!rendition.value) return;

    rendition.value.themes.default({
        'body': { 
            'color': `${textColor.value} !important`, 
            'background': `${backgroundColor.value} !important` 
        },
        'p': {
            'font-family': `${fontName.value} !important`,
            'font-size': `${fontSize.value}% !important`,
            'line-height': `${lineHeight.value} !important`,
        }
    });

    rendition.value.themes.fontSize(`${fontSize.value}%`);
};

// Xử lý chuyển đổi chế độ xem
const updateViewMode = () => {
    if (!rendition.value) return;
    
    try {
        if (viewMode.value === 'scroll') {
            rendition.value.flow('scrolled-doc');
        } else {
            rendition.value.flow('paginated');
            rendition.value.spread(viewMode.value === 'single' ? 'none' : 'auto');
        }
        
        if (viewerRef.value) {
            rendition.value.resize(viewerRef.value.clientWidth, viewerRef.value.clientHeight);
        }
    } catch (e) {
        console.warn("Lỗi chuyển đổi View Mode:", e);
    }
};

// Watchers
watch([backgroundColor, textColor, fontName, fontSize, lineHeight], applySettings);
watch(viewMode, updateViewMode);

// Helpers tăng giảm font
const increaseFont = () => { if(fontSize.value < 200) fontSize.value += 10; };
const decreaseFont = () => { if(fontSize.value > 50) fontSize.value -= 10; };

// CSS Filter cho độ sáng
const brightnessStyle = computed(() => {
    return { filter: `brightness(${brightness.value}%)` };
});

</script>

<template>
    <!-- Container Chính -->
    <div class="relative w-screen h-screen overflow-hidden transition-colors duration-300"
         :style="{ backgroundColor: backgroundColor }"
    >
        
        <!-- HEADER (Top Bar - Luôn hiện) -->
        <div class="absolute top-0 left-0 right-0 h-14 bg-transparent border-b-0 flex items-center justify-between px-4 z-50">
            <!-- Group Trái: Back & Menu -->
            <div class="flex items-center gap-3">
                <button @click="emit('close')" class="text-gray-600 hover:text-black dark:text-gray-400 dark:hover:text-white transition-colors" title="Thoát">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                </button>
                <button @click="showTOC = !showTOC; showSettings = false" class="text-gray-600 hover:text-black dark:text-gray-400 dark:hover:text-white transition-colors" title="Mục lục">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
                </button>
            </div>

            <!-- Group Phải: Fullscreen & Settings -->
            <div class="flex items-center gap-4">
                <button @click="toggleFullscreen" class="text-gray-600 hover:text-black dark:text-gray-400 dark:hover:text-white transition-colors" :title="isFullscreen ? 'Thoát toàn màn hình' : 'Toàn màn hình'">
                    <svg v-if="!isFullscreen" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                </button>

                <button @click="showSettings = !showSettings; showTOC = false" class="text-gray-600 hover:text-black dark:text-gray-400 dark:hover:text-white transition-colors" title="Cài đặt giao diện">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                </button>
            </div>
        </div>

        <!-- SETTINGS SIDEBAR (Drawer bên phải) -->
        <transition name="slide-left">
            <div v-if="showSettings" class="absolute top-0 right-0 bottom-0 w-80 bg-white shadow-2xl z-50 overflow-y-auto border-l flex flex-col">
                <!-- Header Sidebar -->
                <div class="p-4 border-b flex items-center justify-between">
                    <h2 class="font-bold text-gray-700 text-lg">Reading Option</h2>
                    <button @click="showSettings = false" class="text-gray-400 hover:text-gray-600">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>

                <!-- Content Sidebar -->
                <div class="p-5 space-y-6 flex-1">
                    <!-- 1. Chế độ xem -->
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-2">Chế độ xem</label>
                        <div class="grid grid-cols-3 gap-2">
                            <button @click="viewMode = 'single'" :class="viewMode === 'single' ? 'border-red-400 text-red-500' : 'border-gray-300 text-gray-600'" class="border rounded py-3 text-xs font-medium hover:bg-gray-50 flex flex-col items-center justify-center h-20 transition">
                                <span class="block w-6 h-8 border border-current mb-1 bg-gray-100"></span>
                                Một trang
                            </button>
                            <button @click="viewMode = 'double'" :class="viewMode === 'double' ? 'border-red-400 text-red-500' : 'border-gray-300 text-gray-600'" class="border rounded py-3 text-xs font-medium hover:bg-gray-50 flex flex-col items-center justify-center h-20 transition">
                                <span class="flex gap-0.5 mb-1"><span class="w-3 h-8 border border-current bg-gray-100"></span><span class="w-3 h-8 border border-current bg-gray-100"></span></span>
                                Hai trang
                            </button>
                            <button @click="viewMode = 'scroll'" :class="viewMode === 'scroll' ? 'border-red-400 text-red-500' : 'border-gray-300 text-gray-600'" class="border rounded py-3 text-xs font-medium hover:bg-gray-50 flex flex-col items-center justify-center h-20 transition">
                                <span class="block w-6 h-8 border border-current mb-1 border-t-0 border-b-0 bg-gray-100"></span>
                                Cuộn
                            </button>
                        </div>
                    </div>

                    <!-- 2. Kích thước chữ -->
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-2">Kích thước chữ</label>
                        <div class="flex items-center justify-between">
                            <button @click="decreaseFont" class="w-12 h-10 border rounded hover:bg-gray-100 text-xl font-bold text-gray-600">-</button>
                            <span class="text-lg font-bold text-gray-700">{{ fontSize }}</span>
                            <button @click="increaseFont" class="w-12 h-10 border rounded hover:bg-gray-100 text-xl font-bold text-gray-600">+</button>
                        </div>
                    </div>

                    <!-- 3. Màu nền -->
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-2">Màu nền</label>
                        <div class="flex gap-4">
                            <button @click="backgroundColor = '#ffffff'" :class="{'ring-2 ring-blue-500': backgroundColor === '#ffffff'}" class="w-10 h-10 rounded-full border bg-white shadow-sm"></button>
                            <button @click="backgroundColor = '#1a1a1a'" :class="{'ring-2 ring-blue-500': backgroundColor === '#1a1a1a'}" class="w-10 h-10 rounded-full border bg-[#1a1a1a] shadow-sm"></button>
                            <button @click="backgroundColor = '#f6f1d1'" :class="{'ring-2 ring-blue-500': backgroundColor === '#f6f1d1'}" class="w-10 h-10 rounded-full border bg-[#f6f1d1] shadow-sm"></button>
                            <button @click="backgroundColor = '#e2f0e0'" :class="{'ring-2 ring-blue-500': backgroundColor === '#e2f0e0'}" class="w-10 h-10 rounded-full border bg-[#e2f0e0] shadow-sm"></button>
                        </div>
                    </div>

                    <!-- 4. Màu chữ -->
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-2">Màu chữ</label>
                        <div class="flex gap-4">
                            <button @click="textColor = '#ffffff'" :class="{'ring-2 ring-blue-500': textColor === '#ffffff'}" class="w-10 h-10 rounded-full border bg-white shadow-sm"></button>
                            <button @click="textColor = '#1a1a1a'" :class="{'ring-2 ring-blue-500': textColor === '#1a1a1a'}" class="w-10 h-10 rounded-full border bg-[#1a1a1a] shadow-sm"></button>
                            <button @click="textColor = '#5f4b32'" :class="{'ring-2 ring-blue-500': textColor === '#5f4b32'}" class="w-10 h-10 rounded-full border bg-[#5f4b32] shadow-sm"></button>
                            <button @click="textColor = '#2c4c3b'" :class="{'ring-2 ring-blue-500': textColor === '#2c4c3b'}" class="w-10 h-10 rounded-full border bg-[#2c4c3b] shadow-sm"></button>
                        </div>
                    </div>

                    <!-- 5. Làm mờ -->
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-2">Làm mờ</label>
                        <input type="range" v-model="brightness" min="30" max="100" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-orange-500">
                    </div>

                    <!-- 6. Font chữ -->
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-2">Font chữ</label>
                        <select v-model="fontName" class="w-full border p-2 rounded bg-white text-gray-700 focus:outline-none focus:border-blue-500">
                            <option v-for="font in fontOptions" :key="font.value" :value="font.value">{{ font.label }}</option>
                        </select>
                    </div>

                    <!-- 7. Line height -->
                    <div>
                        <label class="block text-sm font-bold text-gray-600 mb-2">Line height</label>
                        <select v-model="lineHeight" class="w-full border p-2 rounded bg-white text-gray-700 focus:outline-none focus:border-blue-500">
                            <option v-for="lh in lineHeightOptions" :key="lh" :value="lh">{{ lh }}</option>
                        </select>
                    </div>
                </div>
            </div>
        </transition>

        <!-- TOC SIDEBAR -->
        <transition name="slide-right">
            <div v-if="showTOC" class="absolute top-0 left-0 bottom-0 w-80 bg-white shadow-2xl z-50 overflow-y-auto border-r">
                <div class="p-4 border-b font-bold text-lg text-gray-800 flex justify-between items-center">
                    <span>Mục Lục</span>
                    <button @click="showTOC = false" class="text-gray-400 hover:text-gray-600">✕</button>
                </div>
                <ul>
                    <li v-for="(item, index) in toc" :key="index">
                        <button @click="goToChapter(item.href)" class="w-full text-left px-4 py-3 hover:bg-gray-50 text-sm border-b border-gray-100 truncate text-gray-700">
                            {{ item.label }}
                        </button>
                    </li>
                </ul>
            </div>
        </transition>

        <!-- VIEWER AREA -->
        <div class=" h-full flex items-center justify-center py-16" :style="brightnessStyle">
            <div ref="viewerRef" class="w-full h-full max-w-6xl mx-auto book-content transition-all duration-300"></div>
        </div>

        <!-- FOOTER (Thanh điều hướng tối màu, luôn hiện, không có thanh tiến độ) -->
        <div class="absolute bottom-0 left-0 right-0 h-14 bg-[#1a1a1a] border-t border-gray-700 flex items-center justify-between px-6 z-40 text-gray-400">
            
            <!-- Nút Trái -->
            <button @click="prevPage" class="p-2 hover:text-white transition-colors" title="Trang trước">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
            </button>

            <!-- Khoảng trống ở giữa (Đã bỏ thanh tiến độ) -->
            <div class="flex-1"></div>

            <!-- Nút Phải -->
            <button @click="nextPage" class="p-2 hover:text-white transition-colors" title="Trang sau">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
            </button>

        </div>

        <!-- Loading -->
        <div v-if="!isReady" class="absolute inset-0 bg-white z-[60] flex items-center justify-center">
            <div class="flex flex-col items-center">
                <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-2"></div>
                <span class="text-gray-500 text-sm">Đang tải sách...</span>
            </div>
        </div>

    </div>
</template>

<style>
/* Animations */
.slide-down-enter-active, .slide-down-leave-active,
.slide-up-enter-active, .slide-up-leave-active,
.slide-right-enter-active, .slide-right-leave-active,
.slide-left-enter-active, .slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from, .slide-down-leave-to { transform: translateY(-100%); opacity: 0; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); opacity: 0; }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(-100%); opacity: 0; }
.slide-left-enter-from, .slide-left-leave-to { transform: translateX(100%); opacity: 0; }

.epub-container {
    overflow: hidden !important; 
}

/* Range slider */
input[type=range] {
  height: 6px;
  background: #e5e7eb;
  border-radius: 5px;
  background-image: linear-gradient(#f97316, #f97316);
  background-size: 100% 100%;
  background-repeat: no-repeat;
}
</style>