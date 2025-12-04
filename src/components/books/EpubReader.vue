<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from "vue";
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

// --- KHỞI TẠO COMPOSABLES (Thư viện xử lý sách) ---
const {
    rendition, book, isReady, toc,
    initEpub, displayBook, prevPage, nextPage,
    goToChapter, goToCfi, setStyle, resizeBook,
    drawAnnotations, removeAnnotationByCfi
} = useEpub();

const { userInfo } = useAuth();
const viewerRef = ref<HTMLElement | null>(null);

// --- TRẠNG THÁI GIAO DIỆN (UI STATE) ---
// Gom nhóm các biến điều khiển hiển thị
const showTOC = ref(false);            // Hiện mục lục
const showSettings = ref(false);       // Hiện cài đặt
const isFullscreen = ref(false);       // Toàn màn hình
const activeSidebarTab = ref<"toc" | "highlight" | "note">("toc"); // Tab đang chọn

// Trạng thái xử lý Highlight/Note
const showSelectionMenu = ref(false);  // Menu hiện ra khi bôi đen text
const currentSelection = ref<{ cfiRange: string; text: string } | null>(null);
const showNotePopup = ref(false);      // Popup xem chi tiết ghi chú
const activeNoteData = ref<{ note: string; excerpt: string; date: string } | null>(null);

// Biến cờ (Flag) để xử lý logic sự kiện
const isTurningPage = ref(false);      // Đang chuyển trang (để chặn cuộn chuột liên tục)
let isHighlightClicked = false;        // Cờ quan trọng: Phân biệt giữa click vào sách và click vào note
let isMouseDown = false;               // Cờ kiểm tra xem chuột có đang nhấn giữ không

// --- DỮ LIỆU (DATA) ---
const highlights = ref<any[]>([]);
const notes = ref<any[]>([]);

// --- CẤU HÌNH HIỂN THỊ (SETTINGS) ---
const viewMode = ref<"single" | "double">("single");
const fontSize = ref(100);
const fontName = ref("Helvetica, Arial, sans-serif");
const lineHeight = ref(1.5);
const backgroundColor = ref("#ffffff");
const textColor = ref("#000000");
const brightness = ref(100);

// Danh sách font chữ hỗ trợ
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

// --- CÁC HÀM XỬ LÝ API (BACKEND) ---

// 1. Tải danh sách Highlight/Note của user
const fetchUserData = async () => {
    if (!props.bookId || !currentUserId.value) return;
    try {
        const res = await axios.get(
            `${BOOK_SERVICE_URL}books/${props.bookId}/annotations/${currentUserId.value}`
        );
        // Tách data trả về thành 2 mảng riêng biệt để dễ quản lý
        highlights.value = res.data.filter((i: any) => i.type === "highlight");
        notes.value = res.data
            .filter((i: any) => i.type === "note")
            .map((i: any) => ({
                ...i,
                excerpt: i.text_content, // Map lại tên trường cho khớp logic hiển thị
                note: i.note_content,
            }));
        // Vẽ lại lên sách sau khi có dữ liệu
        setTimeout(() => drawAnnotations(highlights.value, notes.value), 200);
    } catch (e) {
        console.error("Lỗi tải dữ liệu annotation:", e);
    }
};

// 2. Lưu Annotation mới
const saveAnnotation = async (payload: any) => {
    try {
        const res = await axios.post(`${BOOK_SERVICE_URL}books/annotations/add`, {
            user_id: currentUserId.value,
            book_id: props.bookId,
            ...payload,
        });
        return res.data;
    } catch (e) {
        console.error("Lỗi lưu annotation:", e);
        return null;
    }
};

// 3. Xóa Annotation
const deleteAnnotation = async (id: number) => {
    try {
        await axios.delete(`${BOOK_SERVICE_URL}books/annotations/delete/${id}`);
    } catch (e) { 
        console.error("Lỗi xóa annotation:", e);
    }
};

// --- CÁC HÀM XỬ LÝ GIAO DIỆN (UI HANDLERS) ---

// Cập nhật giao diện sách khi thay đổi setting
const updateUI = () => {
    setStyle({
        fontSize: fontSize.value,
        fontName: fontName.value,
        bg: backgroundColor.value,
        color: textColor.value,
        lineHeight: lineHeight.value,
    });
    if (viewerRef.value && rendition.value) {
        resizeBook(viewerRef.value.clientWidth, viewerRef.value.clientHeight, viewMode.value);
        // Cần vẽ lại annotation vì vị trí text có thể bị lệch khi resize
        setTimeout(() => drawAnnotations(highlights.value, notes.value), 300);
    }
};

// Debounce resize (chờ user dừng kéo cửa sổ mới render lại để tránh giật)
let resizeTimer: any = null;
const handleResize = () => {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        if (viewerRef.value) updateUI();
    }, 200);
};

// Xử lý cuộn chuột để chuyển trang
const handleWheel = (e: WheelEvent) => {
    // Không chuyển trang nếu đang mở menu hoặc đang trong animation
    if (showTOC.value || showSettings.value || isTurningPage.value) return;
    if (Math.abs(e.deltaY) < 30) return; // Bỏ qua các rung động nhỏ của touchpad

    isTurningPage.value = true;
    if (e.deltaY > 0) nextPage();
    else prevPage();

    setTimeout(() => isTurningPage.value = false, 500);
};

// --- LOGIC HIGHLIGHT & NOTE ---

const addHighlight = async () => {
    if (!currentSelection.value) return;
    const payload = {
        cfi_range: currentSelection.value.cfiRange,
        text_content: currentSelection.value.text.substring(0, 100), // Chỉ lấy 100 ký tự đầu làm trích dẫn
        type: "highlight",
        color: "yellow",
    };
    
    // Gọi API lưu
    const saved = await saveAnnotation(payload);
    if (saved) {
        highlights.value.push(saved);
        // Sau khi lưu thành công: Ẩn menu chọn, mở sidebar highlight
        showSelectionMenu.value = false;
        activeSidebarTab.value = "highlight";
        showTOC.value = true;
        updateUI(); // Vẽ lại giao diện
    }
};

const addNote = async () => {
    if (!currentSelection.value) return;
    const noteText = prompt("Nhập ghi chú của bạn:");
    if (!noteText) return; // User ấn Cancel

    const payload = {
        cfi_range: currentSelection.value.cfiRange,
        text_content: currentSelection.value.text.substring(0, 100),
        note_content: noteText,
        type: "note",
        color: "blue",
    };

    const saved = await saveAnnotation(payload);
    if (saved) {
        notes.value.push({
            ...saved,
            excerpt: saved.text_content,
            note: saved.note_content,
        });
        showSelectionMenu.value = false;
        activeSidebarTab.value = "note";
        showTOC.value = true;
        updateUI();
    }
};

const removeItem = async (item: any, type: "highlight" | "note") => {
    // Logic: Xóa trên giao diện TRƯỚC -> Gọi API SAU (Tạo cảm giác phản hồi nhanh)
    
    // 1. Xóa khỏi sách (Visual)
    if (item.cfi_range) {
        removeAnnotationByCfi(item.cfi_range);
    }

    // 2. Xóa khỏi danh sách quản lý
    if (type === "highlight") {
        highlights.value = highlights.value.filter((h) => h.id !== item.id);
    } else {
        notes.value = notes.value.filter((n) => n.id !== item.id);
    }

    // 3. Gọi API xóa ngầm
    if (item.id) {
        await deleteAnnotation(item.id);
    }
};

const toggleFullscreen = () => {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen();
    else if (document.exitFullscreen) document.exitFullscreen();
    isFullscreen.value = !isFullscreen.value;
};

// --- XỬ LÝ SỰ KIỆN CHUỘT & MENU CHỌN TEXT ---
const menuPos = ref({ x: 0, y: 0 });
const tempSelection = ref<{ cfiRange: string; text: string; rect: DOMRect } | null>(null);

onMounted(async () => {
    if (!viewerRef.value) return;

    // 1. Khởi tạo sách
    const r = await initEpub(props.url, viewerRef.value as any);
    if (!r) return;

    // 2. Lắng nghe sự kiện "selected" (Khi user bôi đen văn bản)
    r.on("selected", (cfiRange: string, contents: any) => {
        // Nếu sự kiện này kích hoạt do user click vào highlight cũ -> Bỏ qua
        if (isHighlightClicked) {
            contents.window.getSelection().removeAllRanges();
            return;
        }

        const selection = contents.window.getSelection();
        const text = selection ? selection.toString() : "";

        if (text && text.trim().length > 0) {
            // Lấy tọa độ của đoạn văn bản vừa chọn
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();

            // Lưu tạm vào biến tempSelection (chưa hiện menu ngay)
            tempSelection.value = { cfiRange, text, rect };
            
            // Nếu chuột đã thả ra -> Xử lý hiện menu luôn
            if (!isMouseDown) {
                processSelectionMenu();
            }
        }
    });

    // Hàm tính toán vị trí và hiển thị menu chọn (Highlight/Note)
    const processSelectionMenu = () => {
        if (!tempSelection.value || !viewerRef.value) return;

        currentSelection.value = { 
            cfiRange: tempSelection.value.cfiRange, 
            text: tempSelection.value.text 
        };

        // Tính toán tọa độ menu dựa trên iframe và đoạn text
        try {
            const iframe = viewerRef.value.querySelector("iframe");
            const iframeRect = iframe ? iframe.getBoundingClientRect() : { left: 0, top: 0 };
            
            menuPos.value = {
                // Canh giữa đoạn text
                x: tempSelection.value.rect.left + iframeRect.left + (tempSelection.value.rect.width / 2),
                // Nằm phía trên đoạn text 50px
                y: tempSelection.value.rect.top + iframeRect.top - 50
            };
        } catch (e) {
            // Fallback nếu lỗi: hiện giữa màn hình
            menuPos.value = { x: window.innerWidth / 2, y: 200 };
        }

        // Hiện menu, ẩn các thành phần khác
        showSelectionMenu.value = true;
        showTOC.value = false;
        showSettings.value = false;
        showNotePopup.value = false;
        
        tempSelection.value = null; // Reset temp
    };

    // 3. Sự kiện chuyển trang (Cập nhật tiến độ)
    r.on("relocated", (location: any) => {
        emit("location-change", location.start.cfi);
        // Vẽ lại highlight khi qua trang mới
        setTimeout(() => drawAnnotations(highlights.value, notes.value), 200);
    });

    // 4. Sự kiện click vào Highlight/Note đã có
    r.on("markClicked", (cfiRange: string, data: any) => {
        // [QUAN TRỌNG] Đánh dấu đang click vào note để chặn sự kiện click nền
        isHighlightClicked = true;

        if (data && data.type === "note") {
            const foundNote = notes.value.find((n) => n.id === data.id);
            if (foundNote) {
                activeNoteData.value = {
                    note: foundNote.note,
                    excerpt: foundNote.excerpt,
                    date: new Date(foundNote.created_at).toLocaleDateString("vi-VN"),
                };
                showNotePopup.value = true; // Hiện popup chi tiết
                showSelectionMenu.value = false; // Ẩn menu tạo mới
            }
        } else if (data && data.type === "highlight") {
             // Logic xóa highlight nhanh khi click vào
             if(confirm("Bạn có muốn xóa highlight này không?")) {
                 removeItem(data, 'highlight');
             }
        }

        // Reset cờ sau 300ms
        setTimeout(() => { isHighlightClicked = false; }, 300);
    });

    // 5. Đăng ký sự kiện DOM bên trong Iframe (Khó nhất của Epub.js)
    r.hooks.content.register((contents: any) => {
        const win = contents.window;

        // Mousedown: User bắt đầu nhấn chuột -> Ẩn hết các menu cũ
        win.addEventListener("mousedown", () => {
            isMouseDown = true;
            tempSelection.value = null;
            
            showSelectionMenu.value = false;
            showNotePopup.value = false;
            // Chỉ đóng Settings/TOC nếu không phải đang click vào Highlight
            if (!isHighlightClicked) {
                showSettings.value = false;
                showTOC.value = false;
            }
        });

        // Mouseup: User thả chuột -> Kiểm tra xem có bôi đen text không
        win.addEventListener("mouseup", () => {
            isMouseDown = false;
            setTimeout(() => {
                if (tempSelection.value) {
                    processSelectionMenu();
                }
            }, 10);
        });

        // Đồng bộ cuộn chuột và phím điều hướng
        win.addEventListener("wheel", (e: WheelEvent) => handleWheel(e));
        win.addEventListener("keydown", (e: KeyboardEvent) => {
            if (e.key === "ArrowLeft") prevPage();
            if (e.key === "ArrowRight") nextPage();
        });
    });

    // Load sách và dữ liệu user
    await displayBook(props.initialLocation);
    if (currentUserId.value) await fetchUserData();

    // Set layout ban đầu
    updateUI();
    window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
    window.removeEventListener("resize", handleResize);
    if (resizeTimer) clearTimeout(resizeTimer);
    if (book.value) book.value.destroy();
});

// Tự động cập nhật UI khi settings thay đổi
watch([fontSize, fontName, lineHeight, backgroundColor, textColor, viewMode], () =>
    updateUI()
);
</script>

<template>
    <div class="relative w-screen h-screen overflow-hidden flex flex-col transition-colors duration-300"
        :style="[{ backgroundColor: backgroundColor }]" @wheel="handleWheel">
        
        <div class="absolute inset-0 z-30 pointer-events-none bg-black transition-opacity duration-200"
            :style="{ opacity: (100 - brightness) / 100 }"></div>

        <div class="h-14 shrink-0 flex items-center justify-between px-4 z-50 border-b border-gray-500/10 bg-white/5 backdrop-blur-sm">
            <div class="flex items-center gap-2">
                <button @click="emit('close')" class="p-2 rounded-full hover:bg-black/5 transition text-gray-500 hover:text-gray-900">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                </button>
                <button @click="showTOC = !showTOC; showSettings = false;" class="p-2 rounded-full hover:bg-black/5 transition text-gray-500 hover:text-gray-900">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                </button>
            </div>
            
            <transition name="slide-down">
                <div v-if="showSelectionMenu"
                    class="absolute top-16 left-1/2 -translate-x-1/2 bg-white shadow-xl rounded-lg border border-gray-100 p-1.5 flex gap-2 z-[60] animate-bounce-sm">
                    <button @click="addHighlight" class="flex items-center gap-1.5 bg-yellow-100 hover:bg-yellow-200 text-yellow-800 px-3 py-1.5 rounded-md text-sm font-semibold transition-colors">
                        Highlight
                    </button>
                    <button @click="addNote" class="flex items-center gap-1.5 bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1.5 rounded-md text-sm font-semibold transition-colors">
                        Note
                    </button>
                </div>
            </transition>

            <div class="flex items-center gap-2">
                <button @click="toggleFullscreen" class="p-2 rounded-full hover:bg-black/5 transition text-gray-500 hover:text-gray-900">
                    <svg v-if="!isFullscreen" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                    </svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                </button>
                <button @click="showSettings = !showSettings; showTOC = false;" class="p-2 rounded-full hover:bg-black/5 transition text-gray-500 hover:text-gray-900">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                </button>
            </div>
        </div>

        <transition name="fade">
            <div v-if="showSettings" class="absolute inset-0 z-[45] bg-transparent cursor-default" @click="showSettings = false"></div>
        </transition>

        <transition name="slide-left">
            <div v-if="showSettings"
                class="absolute top-0 right-0 bottom-0 w-80 bg-white/95 backdrop-blur shadow-2xl z-50 p-6 border-l flex flex-col overflow-y-auto text-gray-800">
                <div class="flex justify-between items-center mb-8">
                    <h2 class="font-bold text-xl text-gray-900">Cài đặt hiển thị</h2>
                    <button @click="showSettings = false" class="p-1 hover:bg-gray-100 rounded-full transition-colors">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div class="space-y-8">
                    <div>
                        <label class="block text-xs font-bold uppercase text-gray-400 tracking-wider mb-3">Độ sáng</label>
                        <div class="flex items-center gap-3 bg-gray-50 p-3 rounded-xl border border-gray-200">
                            <input type="range" v-model.number="brightness" min="20" max="100" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600 hover:accent-blue-500" />
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-gray-400 tracking-wider mb-3">Chế độ đọc</label>
                        <div class="grid grid-cols-2 gap-3">
                            <button @click="viewMode = 'single'" :class="viewMode === 'single' ? 'bg-blue-50 border-blue-500 text-blue-700 ring-1 ring-blue-500' : 'bg-white border-gray-200 text-gray-600 hover:border-gray-400'" class="flex flex-col items-center justify-center py-4 rounded-xl border transition-all duration-200">
                                <span class="text-xs font-semibold">1 Trang</span>
                            </button>
                            <button @click="viewMode = 'double'" :class="viewMode === 'double' ? 'bg-blue-50 border-blue-500 text-blue-700 ring-1 ring-blue-500' : 'bg-white border-gray-200 text-gray-600 hover:border-gray-400'" class="flex flex-col items-center justify-center py-4 rounded-xl border transition-all duration-200">
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
                        </div>
                    </div>
                </div>
            </div>
        </transition>

        <transition name="fade">
            <div v-if="showTOC" class="absolute inset-0 z-[45] bg-black/20 backdrop-blur-sm cursor-pointer" @click="showTOC = false"></div>
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
                    </ul>
                </div>
            </div>
        </transition>

        <transition name="fade">
            <div v-if="showNotePopup && activeNoteData" class="absolute inset-0 z-[80] flex items-center justify-center p-4 pointer-events-none">
                <div class="absolute inset-0 bg-black/20 backdrop-blur-[2px] pointer-events-auto z-0" @click="showNotePopup = false"></div>
                <div class="bg-white relative z-10 rounded-xl shadow-2xl w-full max-w-md pointer-events-auto flex flex-col overflow-hidden border border-gray-100">
                    <div class="bg-blue-50 px-4 py-3 flex justify-between items-center border-b border-blue-100">
                        <span class="font-bold text-sm uppercase tracking-wide text-blue-800">Ghi chú của bạn</span>
                        <button @click="showNotePopup = false" class="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-white/50 transition">X</button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="relative bg-gray-50 p-4 rounded-lg border-l-4 border-yellow-400">
                            <p class="relative z-10 text-gray-600 italic text-sm font-serif leading-relaxed indent-4">{{ activeNoteData.excerpt }}</p>
                        </div>
                        <div class="pt-1">
                            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Nội dung:</label>
                            <p class="text-gray-800 text-lg font-medium leading-relaxed whitespace-pre-wrap">{{ activeNoteData.note }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </transition>

        <div class="flex-1 relative w-full overflow-hidden flex items-center justify-center z-0">
            <div ref="viewerRef" class="h-full w-full max-w-screen-2xl mx-auto book-content shadow-lg transition-all duration-300"></div>
        </div>

        <div class="h-12 shrink-0 bg-[#1a1a1a]/90 backdrop-blur border-t border-gray-700 flex items-center justify-between px-6 z-40 text-gray-400">
            <button @click="prevPage" class="flex items-center gap-1 px-3 py-1 hover:text-white hover:bg-white/10 rounded transition-colors">
                Trước
            </button>
            <div class="text-xs font-mono opacity-50 select-none">EPUB READER</div>
            <button @click="nextPage" class="flex items-center gap-1 px-3 py-1 hover:text-white hover:bg-white/10 rounded transition-colors">
                Sau
            </button>
        </div>

        <transition name="fade">
            <div v-if="!isReady" class="absolute inset-0 bg-white z-[70] flex flex-col gap-4 items-center justify-center">
                <div class="animate-spin rounded-full h-12 w-12 border-4 border-gray-100 border-t-blue-600"></div>
                <p class="text-gray-400 text-sm font-medium animate-pulse">Đang tải sách...</p>
            </div>
        </transition>
    </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background-color: rgba(0, 0, 0, 0.1); border-radius: 10px; }
.custom-scrollbar:hover::-webkit-scrollbar-thumb { background-color: rgba(0, 0, 0, 0.2); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>