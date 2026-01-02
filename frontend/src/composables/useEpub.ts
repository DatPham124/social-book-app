import { ref } from 'vue';
import ePub, { Book, Rendition } from 'epubjs';

// Định nghĩa kiểu dữ liệu cho Annotation (Giúp code chặt chẽ hơn dùng 'any')
interface AnnotationItem {
    id: number | string;
    cfi_range: string;
    type: 'highlight' | 'note';
    text_content?: string;
    color?: string;
}

export function useEpub() {
    // --- STATE QUẢN LÝ ---
    const book = ref<Book | null>(null);
    const rendition = ref<Rendition | null>(null);
    const isReady = ref(false);
    const toc = ref<any[]>([]); // Table of Contents

    // --- 1. KHỞI TẠO SÁCH (CORE) ---
    const initEpub = async (url: string, element: HTMLElement) => {
        console.group("📚 [Epub System] Khởi tạo sách");
        
        if (!url || !element) {
            console.error("❌ Thiếu URL hoặc DOM Element");
            console.groupEnd();
            return null;
        }

        // Hủy instance cũ để tránh rò rỉ bộ nhớ khi user mở sách khác
        if (book.value) {
            console.log("♻️ Cleanup sách cũ...");
            book.value.destroy();
        }
        isReady.value = false;

        try {
            // Khởi tạo đối tượng Book từ thư viện epubjs
            book.value = ePub(url);
            
            // Render sách vào thẻ div (element)
            rendition.value = book.value.renderTo(element, {
                width: '100%',
                height: '100%',
                flow: 'paginated', // Chế độ lật trang (quan trọng cho trải nghiệm đọc)
                manager: 'default',
            });

            // Đợi load xong mục lục (Navigation)
            const nav = await book.value.loaded.navigation;
            toc.value = nav.toc;
            
            console.log(`✅ Đã tải xong. Số chương: ${nav.toc.length}`);
            console.groupEnd();

            return rendition.value;
        } catch (e) {
            console.error("❌ Lỗi khởi tạo sách:", e);
            console.groupEnd();
            return null;
        }
    };

    // --- 2. ĐIỀU HƯỚNG (NAVIGATION) ---
    
    const displayBook = async (location?: string) => {
        if (!rendition.value) return;
        try {
            // Nếu có location (cfi/href) thì nhảy tới, không thì mở trang đầu
            await rendition.value.display(location);
            isReady.value = true;
        } catch (err) {
            console.warn("⚠️ Vị trí không hợp lệ, quay về trang đầu.");
            await rendition.value.display();
            isReady.value = true;
        }
    };

    const prevPage = () => rendition.value?.prev();
    const nextPage = () => rendition.value?.next();
    
    const goToChapter = (href: string) => {
        console.log("📑 Chuyển chương:", href);
        rendition.value?.display(href);
    };

    const goToCfi = (cfi: string) => {
        console.log("📍 Nhảy tới vị trí (CFI):", cfi);
        rendition.value?.display(cfi);
    };

    // --- 3. GIAO DIỆN & CSS INJECTION (QUAN TRỌNG) ---
    
    /**
     * Hàm này can thiệp vào Iframe của sách để:
     * 1. Đổi font/size/màu nền.
     * 2. [CỰC QUAN TRỌNG] Bật tính năng 'user-select' để cho phép bôi đen văn bản.
     */
    const setStyle = (settings: { 
        fontSize: number; fontName: string; bg: string; color: string; lineHeight: number 
    }) => {
        if (!rendition.value) return;

        // API chuẩn của EpubJS
        rendition.value.themes.font(settings.fontName);
        rendition.value.themes.fontSize(settings.fontSize + "%");

        rendition.value.themes.default({    
            'body': { 
                'color': `${settings.color} !important`, 
                'background': `${settings.bg} !important`,
                'padding': '0 20px !important', 
                
                '-webkit-user-select': 'text !important', 
                'user-select': 'text !important',         
                'cursor': 'auto !important'
            },
            'p': {
                'font-family': `${settings.fontName} !important`, 
                'line-height': `${settings.lineHeight} !important`,
                'font-size': `${settings.fontSize}% !important`,
                'text-align': 'justify !important',
                '-webkit-user-select': 'text !important', 
                'user-select': 'text !important'
            },
            '::selection': {
                'background': 'rgba(66, 135, 245, 0.3)' 
            },
            '.highlight-default': {
                'fill': 'yellow',
                'fill-opacity': '0.3',
                'mix-blend-mode': 'multiply',
                'cursor': 'pointer' 
            },
            '.highlight-default:hover': {
                'fill-opacity': '0.5',
            }
        });
    };

    const resizeBook = (width: number, height: number, viewMode: 'single' | 'double') => {
        if (!rendition.value || width === 0 || height === 0) return;
        rendition.value.resize(width, height);
        rendition.value.spread(viewMode === 'single' ? "none" : "auto");
    };


    const drawAnnotations = (highlights: AnnotationItem[], notes: AnnotationItem[]) => {
        if (!rendition.value) return;

        console.log(`🖊️ Vẽ lại ${highlights.length} highlight và ${notes.length} note.`);
        const annotations = rendition.value.annotations;
        
        const allItems = [...highlights, ...notes];

        allItems.forEach(item => {
            try { 
                annotations.remove(item.cfi_range, 'highlight'); 
            } catch (e) {}
        });

        allItems.forEach((item) => {
            try {
                annotations.add(
                    'highlight', 
                    item.cfi_range, 
                    { id: item.id, type: item.type, text_content: item.text_content }, 
                    undefined, 
                    'highlight-default'
                );
            } catch (e) {
                console.warn(`Lỗi vẽ item ID ${item.id}`, e);
            }
        });
    };

    const removeAnnotationByCfi = (cfiRange: string) => {
        if (!rendition.value) return;
        try {
            // Xóa trực tiếp trên UI (không cần reload API) -> Tăng trải nghiệm người dùng
            rendition.value.annotations.remove(cfiRange, "highlight");
            console.log("🗑️ Đã xóa visual highlight:", cfiRange);
        } catch (e) {
            console.error("Lỗi xóa highlight visual:", e);
        }
    };

    return {
        // State
        book, rendition, isReady, toc,
        // Methods
        initEpub, displayBook, 
        prevPage, nextPage, goToChapter, goToCfi,
        setStyle, resizeBook, 
        drawAnnotations, removeAnnotationByCfi
    };
}