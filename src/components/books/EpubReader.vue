<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from "vue";
import axios from "axios";
import { BOOK_SERVICE_URL } from "../../config";
import { useAuth } from "../../composables/useAuth";
import { useEpub } from "../../composables/useEpub";

// --- PROPS & EMITS ---
const props = defineProps<{
    url: string;
    initialLocation?: string;
    bookId?: string | number;
    userId?: string | number;
}>();
const emit = defineEmits(["close", "location-change"]);

// --- CORE LOGIC ---
const {
    rendition,
    book, // [MỚI] Lấy thêm book ra để destroy khi thoát
    isReady,
    toc,
    initEpub,
    displayBook,
    prevPage,
    nextPage,
    goToChapter,
    goToCfi,
    setStyle,
    resizeBook,
    drawAnnotations,
} = useEpub();

const { userInfo } = useAuth();
const viewerRef = ref<HTMLElement | null>(null);

// --- UI STATE ---
const showTOC = ref(false);
const showSettings = ref(false);
const isFullscreen = ref(false);
const activeSidebarTab = ref<"toc" | "highlight" | "note">("toc");
const showSelectionMenu = ref(false);
const currentSelection = ref<{ cfiRange: string; text: string } | null>(null);
const isTurningPage = ref(false); // Biến chặn cuộn trang quá nhanh

// --- DATA ---
const highlights = ref<any[]>([]);
const notes = ref<any[]>([]);

// --- SETTINGS VALUES ---
const viewMode = ref<"single" | "double">("single");
const fontSize = ref(100);
const fontName = ref("Helvetica, Arial, sans-serif");
const lineHeight = ref(1.5);
const backgroundColor = ref("#ffffff");
const textColor = ref("#000000");
const brightness = ref(100);

const fontOptions = [
    { label: "Mặc định", value: "Helvetica, Arial, sans-serif" },
    { label: "Times New Roman", value: '"Times New Roman", serif' },
    { label: "Arial", value: "Arial, sans-serif" },
    { label: "Verdana", value: "Verdana, sans-serif" },
    { label: "Georgia", value: "Georgia, serif" },
];

// --- COMPUTED ---
const currentUserId = computed(
    () => props.userId || userInfo.value?.id || userInfo.value?.user_id
);

// --- API ---
const fetchUserData = async () => {
    if (!props.bookId || !currentUserId.value) return;
    try {
        const res = await axios.get(
            `${BOOK_SERVICE_URL}books/${props.bookId}/annotations/${currentUserId.value}`
        );
        highlights.value = res.data.filter((i: any) => i.type === "highlight");
        notes.value = res.data
            .filter((i: any) => i.type === "note")
            .map((i: any) => ({
                ...i,
                excerpt: i.text_content,
                note: i.note_content,
            }));
        setTimeout(() => drawAnnotations(highlights.value, notes.value), 200);
    } catch (e) {
        console.error("Load Data Error", e);
    }
};

const saveAnnotation = async (payload: any) => {
    try {
        const res = await axios.post(`${BOOK_SERVICE_URL}books/annotations/add`, {
            user_id: currentUserId.value,
            book_id: props.bookId,
            ...payload,
        });
        return res.data;
    } catch (e) {
        return null;
    }
};

const deleteAnnotation = async (id: number) => {
    try {
        await axios.delete(`${BOOK_SERVICE_URL}books/annotations/delete/${id}`);
    } catch (e) { }
};

// --- HANDLERS UI ---
const updateUI = () => {
    setStyle({
        fontSize: fontSize.value,
        fontName: fontName.value,
        bg: backgroundColor.value,
        color: textColor.value,
        lineHeight: lineHeight.value,
    });
    // [FIX LỖI] Kiểm tra kỹ viewerRef trước khi resize
    if (viewerRef.value && rendition.value) {
        resizeBook(
            viewerRef.value.clientWidth,
            viewerRef.value.clientHeight,
            viewMode.value
        );
        setTimeout(() => drawAnnotations(highlights.value, notes.value), 300);
    }
};

// --- [MỚI] QUẢN LÝ RESIZE AN TOÀN ---
let resizeTimer: any = null;
const handleResize = () => {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        // Chỉ chạy updateUI nếu component chưa bị hủy (viewerRef còn tồn tại)
        if (viewerRef.value) {
            updateUI();
        }
    }, 200);
};

// Hàm xử lý cuộn chuột
const handleWheel = (e: WheelEvent) => {
    if (showTOC.value || showSettings.value) return;
    if (isTurningPage.value) return;
    if (Math.abs(e.deltaY) < 30) return;

    isTurningPage.value = true;

    if (e.deltaY > 0) nextPage();
    else prevPage();

    setTimeout(() => {
        isTurningPage.value = false;
    }, 500);
};

const addHighlight = async () => {
    if (!currentSelection.value) return;
    const payload = {
        cfi_range: currentSelection.value.cfiRange,
        text_content: currentSelection.value.text.substring(0, 100),
        type: "highlight",
        color: "yellow",
    };
    const saved = await saveAnnotation(payload);
    if (saved) highlights.value.push(saved);

    showSelectionMenu.value = false;
    activeSidebarTab.value = "highlight";
    showTOC.value = true;
    updateUI();
};

const addNote = async () => {
    if (!currentSelection.value) return;
    const noteText = prompt("Nhập ghi chú:");
    if (!noteText) return;
    const payload = {
        cfi_range: currentSelection.value.cfiRange,
        text_content: currentSelection.value.text.substring(0, 100),
        note_content: noteText,
        type: "note",
        color: "blue",
    };
    const saved = await saveAnnotation(payload);
    if (saved)
        notes.value.push({
            ...saved,
            excerpt: saved.text_content,
            note: saved.note_content,
        });

    showSelectionMenu.value = false;
    activeSidebarTab.value = "note";
    showTOC.value = true;
    updateUI();
};

const removeItem = async (item: any, type: "highlight" | "note") => {
    if (type === "highlight")
        highlights.value = highlights.value.filter((h) => h.id !== item.id);
    else notes.value = notes.value.filter((n) => n.id !== item.id);
    if (item.id) await deleteAnnotation(item.id);
    updateUI();
};

const toggleFullscreen = () => {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen();
    else if (document.exitFullscreen) document.exitFullscreen();
    isFullscreen.value = !isFullscreen.value;
};

// --- LIFECYCLE HOOKS ---
onMounted(async () => {
    if (!viewerRef.value) return;

    // 1. Init
    const r = await initEpub(props.url, viewerRef.value as any);
    if (!r) return;

    // 2. Events
    r.on("selected", (cfiRange: string, contents: any) => {
        const text = contents.window.getSelection().toString();
        if (text) {
            currentSelection.value = { cfiRange, text };
            showSelectionMenu.value = true;
        }
    });
    r.on("relocated", (location: any) => {
        emit("location-change", location.start.cfi);
        setTimeout(() => drawAnnotations(highlights.value, notes.value), 200);
    });
    
    // Đăng ký sự kiện bên trong Iframe
    r.hooks.content.register((contents: any) => {
        const doc = contents.window.document;
        const win = contents.window;

        win.addEventListener("click", () => {
            showSettings.value = false;
            showTOC.value = false;
            showSelectionMenu.value = false;
        });

        win.addEventListener("wheel", (e: WheelEvent) => {
            handleWheel(e);
        });
        
        win.addEventListener("keydown", (e: KeyboardEvent) => {
            if (e.key === "ArrowLeft") prevPage();
            if (e.key === "ArrowRight") nextPage();
        });
    });

    // 3. Display & Load Data
    await displayBook(props.initialLocation);
    if (currentUserId.value) await fetchUserData();

    // 4. Set Initial Layout
    updateUI();
    
    // [FIX LỖI] Dùng hàm định danh để đăng ký resize
    window.addEventListener("resize", handleResize);
});

// [MỚI] Hook dọn dẹp quan trọng để tránh lỗi
onUnmounted(() => {
    // 1. Gỡ bỏ sự kiện resize
    window.removeEventListener("resize", handleResize);
    
    // 2. Xóa timer đang chạy (nếu có)
    if (resizeTimer) clearTimeout(resizeTimer);

    // 3. Hủy instance sách
    if (book.value) {
        book.value.destroy();
    }
});

watch(
    [fontSize, fontName, lineHeight, backgroundColor, textColor, viewMode],
    () => updateUI()
);
</script>

<template>
    <div class="relative w-screen h-screen overflow-hidden flex flex-col transition-colors duration-300"
         :style="[{ backgroundColor: backgroundColor }]"
         @wheel="handleWheel"> 
         
         <div class="absolute inset-0 z-30 pointer-events-none bg-black transition-opacity duration-200"
             :style="{ opacity: (100 - brightness) / 100 }">
         </div>
         
        <div class="h-14 shrink-0 flex items-center justify-between px-4 z-50 border-b border-gray-500/10 bg-white/5 backdrop-blur-sm">
            <div class="flex items-center gap-2">
                <button @click="emit('close')" class="p-2 rounded-full hover:bg-black/5 transition text-gray-500 hover:text-gray-900" title="Thoát">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                </button>
                <button @click="showTOC = !showTOC; showSettings = false;" class="p-2 rounded-full hover:bg-black/5 transition text-gray-500 hover:text-gray-900" title="Mục lục & Ghi chú">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
                </button>
            </div>
            <transition name="slide-down">
                <div v-if="showSelectionMenu"
                    class="absolute top-16 left-1/2 -translate-x-1/2 bg-white shadow-xl rounded-lg border border-gray-100 p-1.5 flex gap-2 z-[60] animate-bounce-sm">
                    <button @click="addHighlight"
                        class="flex items-center gap-1.5 bg-yellow-100 hover:bg-yellow-200 text-yellow-800 px-3 py-1.5 rounded-md text-sm font-semibold transition-colors">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        Highlight
                    </button>
                    <button @click="addNote"
                        class="flex items-center gap-1.5 bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1.5 rounded-md text-sm font-semibold transition-colors">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        Note
                    </button>
                </div>
            </transition>

            <div class="flex items-center gap-2">
                <button @click="toggleFullscreen"
                    class="p-2 rounded-full hover:bg-black/5 transition text-gray-500 hover:text-gray-900">
                    <svg v-if="!isFullscreen" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none"
                        viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                    </svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24"
                        stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                </button>
                <button @click="showSettings = !showSettings; showTOC = false;" class="p-2 rounded-full hover:bg-black/5 transition text-gray-500 hover:text-gray-900" title="Cài đặt">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                </button>
            </div>
        </div>

        <transition name="slide-left">
            <div v-if="showSettings" class="absolute top-0 right-0 bottom-0 w-80 bg-white/95 backdrop-blur shadow-2xl z-50 p-6 border-l flex flex-col overflow-y-auto text-gray-800">
                <div class="flex justify-between items-center mb-8">
                    <h2 class="font-bold text-xl text-gray-900">Cài đặt hiển thị</h2>
                    <button @click="showSettings = false" class="p-1 hover:bg-gray-100 rounded-full">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                 <div class="space-y-8">
                    <div>
                        <label class="block text-xs font-bold uppercase text-gray-400 tracking-wider mb-3">Độ sáng</label>
                        <div class="flex items-center gap-3 bg-gray-50 p-3 rounded-xl border border-gray-200">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                            </svg>
                            <input type="range" v-model.number="brightness" min="20" max="100" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600 hover:accent-blue-500">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                            </svg>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-gray-400 tracking-wider mb-3">Chế độ đọc</label>
                        <div class="grid grid-cols-2 gap-3">
                            <button @click="viewMode = 'single'" :class="viewMode === 'single' ? 'bg-blue-50 border-blue-500 text-blue-700 ring-1 ring-blue-500' : 'bg-white border-gray-200 text-gray-600 hover:border-gray-400'" class="flex flex-col items-center justify-center py-4 rounded-xl border transition-all duration-200">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                                <span class="text-xs font-semibold">1 Trang</span>
                            </button>
                            <button @click="viewMode = 'double'" :class="viewMode === 'double' ? 'bg-blue-50 border-blue-500 text-blue-700 ring-1 ring-blue-500' : 'bg-white border-gray-200 text-gray-600 hover:border-gray-400'" class="flex flex-col items-center justify-center py-4 rounded-xl border transition-all duration-200">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                                <span class="text-xs font-semibold">2 Trang</span>
                            </button>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-gray-400 tracking-wider mb-3">Cỡ chữ: {{ fontSize }}%</label>
                        <div class="flex items-center border border-gray-200 rounded-lg p-1 bg-gray-50">
                            <button @click="fontSize > 50 ? (fontSize -= 10) : null" class="w-12 h-10 flex items-center justify-center hover:bg-white hover:shadow-sm rounded transition font-serif text-lg">-</button>
                            <div class="flex-1 h-4 bg-gray-200 rounded-full mx-2 relative overflow-hidden">
                                <div class="absolute top-0 left-0 h-full bg-blue-500 transition-all" :style="{ width: ((fontSize - 50) / 150) * 100 + '%' }"></div>
                            </div>
                            <button @click="fontSize < 200 ? (fontSize += 10) : null" class="w-12 h-10 flex items-center justify-center hover:bg-white hover:shadow-sm rounded transition font-serif text-xl">+</button>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-gray-400 tracking-wider mb-3">Màu nền</label>
                        <div class="flex gap-4">
                            <button @click="backgroundColor = '#ffffff'; textColor = '#000000';" class="w-12 h-12 rounded-full border-2 bg-white shadow-sm ring-offset-2 hover:scale-105 transition" :class="backgroundColor === '#ffffff' ? 'ring-2 ring-blue-500 border-blue-200' : 'border-gray-200'"></button>
                            <button @click="backgroundColor = '#f6f1d1'; textColor = '#5f4b32';" class="w-12 h-12 rounded-full border-2 bg-[#f6f1d1] shadow-sm ring-offset-2 hover:scale-105 transition" :class="backgroundColor === '#f6f1d1' ? 'ring-2 ring-blue-500 border-yellow-200' : 'border-transparent'"></button>
                            <button @click="backgroundColor = '#1a1a1a'; textColor = '#e5e5e5';" class="w-12 h-12 rounded-full border-2 bg-[#1a1a1a] shadow-sm ring-offset-2 hover:scale-105 transition" :class="backgroundColor === '#1a1a1a' ? 'ring-2 ring-blue-500 border-gray-600' : 'border-transparent'"></button>
                        </div>
                    </div>
                     <div>
                        <label class="block text-xs font-bold uppercase text-gray-400 tracking-wider mb-3">Kiểu chữ</label>
                        <div class="relative">
                            <select v-model="fontName" class="w-full appearance-none bg-white border border-gray-200 text-gray-700 py-3 px-4 pr-8 rounded-lg leading-tight focus:outline-none focus:bg-white focus:border-blue-500">
                                <option v-for="f in fontOptions" :value="f.value" :key="f.value">{{ f.label }}</option>
                            </select>
                            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                                <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /></svg>
                            </div>
                        </div>
                    </div>
                 </div>
            </div>
        </transition>

         <transition name="slide-right">
             <div v-if="showTOC" class="absolute top-0 left-0 bottom-0 w-80 bg-white shadow-2xl z-50 flex flex-col border-r border-gray-100 text-gray-800 font-sans">
                 <div class="flex p-2 bg-gray-50 border-b border-gray-100 gap-1">
                    <button @click="activeSidebarTab = 'toc'" :class="activeSidebarTab === 'toc' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:bg-gray-200/50'" class="flex-1 py-2 rounded-md text-sm font-semibold transition-all">Mục lục</button>
                    <button @click="activeSidebarTab = 'highlight'" :class="activeSidebarTab === 'highlight' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:bg-gray-200/50'" class="flex-1 py-2 rounded-md text-sm font-semibold transition-all">Highlight</button>
                    <button @click="activeSidebarTab = 'note'" :class="activeSidebarTab === 'note' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:bg-gray-200/50'" class="flex-1 py-2 rounded-md text-sm font-semibold transition-all">Ghi chú</button>
                </div>
                 <div class="flex-1 overflow-y-auto custom-scrollbar bg-white">
                     <ul v-if="activeSidebarTab === 'toc'" class="py-2">
                        <li v-for="(item, idx) in toc" :key="idx" class="group">
                            <button @click="goToChapter(item.href)" class="w-full text-left px-5 py-3 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 transition-colors flex items-start gap-3">
                                <span class="mt-0.5 text-gray-300 group-hover:text-blue-400"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg></span>
                                <span class="flex-1 leading-relaxed">{{ item.label }}</span>
                            </button>
                        </li>
                        <li v-if="toc.length === 0" class="p-8 text-center text-gray-400 text-sm">Đang tải mục lục...</li>
                    </ul>
                     <ul v-if="activeSidebarTab === 'highlight'" class="space-y-1 p-2">
                         <li v-for="h in highlights" :key="h.id" class="p-4 rounded-lg hover:bg-gray-50 cursor-pointer border border-transparent hover:border-gray-100 transition-all group" @click="goToCfi(h.cfi_range)">
                            <div class="flex gap-2 mb-2">
                                <div class="w-1 h-auto bg-yellow-400 rounded-full"></div>
                                <p class="text-sm text-gray-800 italic font-serif leading-relaxed line-clamp-3">"{{ h.text_content }}"</p>
                            </div>
                            <div class="flex justify-between items-center mt-2 pl-3">
                                <span class="text-xs text-gray-400">{{ new Date(h.created_at).toLocaleDateString("vi-VN") }}</span>
                                <button @click.stop="removeItem(h, 'highlight')" class="text-xs text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity uppercase font-bold px-2 py-1">Xóa</button>
                            </div>
                        </li>
                        <li v-if="highlights.length === 0" class="p-8 text-center text-gray-400 text-sm">Chưa có highlight nào</li>
                     </ul>
                      <ul v-if="activeSidebarTab === 'note'" class="space-y-1 p-2">
                        <li v-for="n in notes" :key="n.id" class="p-4 rounded-lg hover:bg-gray-50 cursor-pointer border border-transparent hover:border-gray-100 transition-all group" @click="goToCfi(n.cfi_range)">
                            <div class="flex gap-2 mb-1">
                                <div class="w-1 h-auto bg-blue-500 rounded-full"></div>
                                <p class="text-xs text-gray-500 italic line-clamp-1">Trích: "{{ n.excerpt }}"</p>
                            </div>
                            <p class="text-sm font-semibold text-gray-800 pl-3 mb-1">{{ n.note }}</p>
                            <div class="flex justify-between items-center mt-2 pl-3">
                                <span class="text-xs text-gray-400">{{ new Date(n.created_at).toLocaleDateString("vi-VN") }}</span>
                                <button @click.stop="removeItem(n, 'note')" class="text-xs text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity uppercase font-bold px-2 py-1">Xóa</button>
                            </div>
                        </li>
                        <li v-if="notes.length === 0" class="p-8 text-center text-gray-400 text-sm">Chưa có ghi chú nào</li>
                    </ul>
                 </div>
                 <div class="p-4 border-t border-gray-100">
                    <button @click="showTOC = false" class="w-full py-2 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg text-sm font-bold transition">Đóng Sidebar</button>
                </div>
             </div>
        </transition>

        <div class="flex-1 relative w-full overflow-hidden flex items-center justify-center z-0">
            <div class="absolute inset-y-0 left-0 w-16 z-20 cursor-pointer hover:bg-gradient-to-r from-black/5 to-transparent transition-opacity opacity-0 hover:opacity-100"
                @click="prevPage" title="Trang trước"></div>
            <div ref="viewerRef" class="h-full w-full max-w-screen-2xl mx-auto book-content shadow-lg transition-all duration-300"></div>
            <div class="absolute inset-y-0 right-0 w-16 z-20 cursor-pointer hover:bg-gradient-to-l from-black/5 to-transparent transition-opacity opacity-0 hover:opacity-100"
                @click="nextPage" title="Trang sau"></div>
        </div>

        <div class="h-12 shrink-0 bg-[#1a1a1a]/90 backdrop-blur border-t border-gray-700 flex items-center justify-between px-6 z-40 text-gray-400">
            <button @click="prevPage" class="flex items-center gap-1 px-3 py-1 hover:text-white hover:bg-white/10 rounded transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
                <span class="text-xs font-medium">Trước</span>
            </button>
            <div class="text-xs font-mono opacity-50 select-none">EPUB READER</div>
            <button @click="nextPage" class="flex items-center gap-1 px-3 py-1 hover:text-white hover:bg-white/10 rounded transition-colors">
                <span class="text-xs font-medium">Sau</span>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
            </button>
        </div>

        <transition name="fade">
            <div v-if="!isReady"
                class="absolute inset-0 bg-white z-[70] flex flex-col gap-4 items-center justify-center">
                <div class="animate-spin rounded-full h-12 w-12 border-4 border-gray-100 border-t-blue-600"></div>
                <p class="text-gray-400 text-sm font-medium animate-pulse">
                    Đang tải sách...
                </p>
            </div>
        </transition>
    </div>
</template>

<style scoped>
/* Code CSS giữ nguyên */
.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: rgba(0, 0, 0, 0.1);
    border-radius: 10px;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
    background-color: rgba(0, 0, 0, 0.2);
}
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>