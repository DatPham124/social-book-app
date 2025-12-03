import { ref, nextTick } from 'vue';
import ePub, { Book, Rendition } from 'epubjs';

export function useEpub() {
    const book = ref<Book | null>(null);
    const rendition = ref<Rendition | null>(null);
    const isReady = ref(false);
    const toc = ref<any[]>([]);
    
    // --- KHỞI TẠO ---
    const initEpub = async (url: string, element: HTMLElement) => {
        console.log("📚 Init Epub với URL:", url);
        if (!url || !element) {
            console.warn("❌ URL hoặc Element thiếu!");
            return null;
        }
        if (book.value) book.value.destroy();
        isReady.value = false;

        try {
            book.value = ePub(url);
            rendition.value = book.value.renderTo(element, {
                width: '100%',
                height: '100%',
                flow: 'paginated',
                manager: 'default',
            });

            // Load Mục lục
            const nav = await book.value.loaded.navigation;
            toc.value = nav.toc;
            console.log("✅ Epub Init thành công, TOC:", nav.toc.length);

            return rendition.value;
        } catch (e) {
            console.error("❌ Lỗi khởi tạo sách:", e);
            return null;
        }
    };

    // --- HIỂN THỊ & ĐIỀU HƯỚNG ---
    const displayBook = async (location?: string) => {
        if (!rendition.value) return;
        try {
            await rendition.value.display(location);
            isReady.value = true;
            console.log("📖 Hiển thị sách tại:", location || "trang đầu");
        } catch (err) {
            console.warn("⚠️ Lỗi hiển thị location, fallback về đầu trang.", err);
            await rendition.value.display(); // Fallback về trang đầu
            isReady.value = true;
        }
    };

    const prevPage = () => rendition.value?.prev();
    const nextPage = () => rendition.value?.next();
    const goToChapter = (href: string) => rendition.value?.display(href);
    const goToCfi = (cfi: string) => rendition.value?.display(cfi);

    // --- GIAO DIỆN & THEME ---
    const setStyle = (settings: { 
        fontSize: number; 
        fontName: string; 
        bg: string; 
        color: string; 
        lineHeight: number 
    }) => {
        if (!rendition.value) return;

        // 1. Dùng API chuẩn
        rendition.value.themes.font(settings.fontName);
        rendition.value.themes.fontSize(settings.fontSize + "%");

        // 2. Override Styles
        rendition.value.themes.default({    
            'body': { 
                'color': `${settings.color} !important`, 
                'background': `${settings.bg} !important`,
                'padding': '10px !important'
            },
            'p': {
                'font-family': `${settings.fontName} !important`, 
                'line-height': `${settings.lineHeight} !important`,
                'font-size': `${settings.fontSize}% !important`,
                'text-align': 'justify !important'
            }
        });

        // 3. Hack: Inject thẳng vào iframe để chắc chắn ăn style (cho body/p)
        const views = (rendition.value as any).getContents();
        if (views) {
            views.forEach((view: any) => {
               if(view.document) {
                    view.document.body.style.fontFamily = settings.fontName;
                    view.document.body.style.lineHeight = settings.lineHeight;
                    view.document.body.style.fontSize = settings.fontSize + "%";
                    view.document.body.style.color = settings.color;
                    view.document.body.style.backgroundColor = settings.bg;
               }
            });
        }
    };

    // Resize & Chế độ xem
    const resizeBook = (width: number, height: number, viewMode: 'single' | 'double') => {
        if (!rendition.value || width === 0 || height === 0) return;

        rendition.value.resize(width, height);
        if (viewMode === 'single') rendition.value.spread("none");
        else rendition.value.spread("auto");
        rendition.value.flow("paginated");
    };

    // --- QUẢN LÝ ANNOTATIONS ---
    const drawAnnotations = (highlights: any[], notes: any[]) => {
        console.group("🖊️ Draw Annotations (Simple Yellow)");
        
        if (!rendition.value) {
            console.error("❌ Rendition chưa sẵn sàng!");
            console.groupEnd();
            return;
        }

        const annotations = rendition.value.annotations;
        const allItems = highlights.concat(notes);

        // 1. Xóa Annotations cũ
        allItems.forEach(item => {
            try { annotations.remove(item.cfi_range, 'highlight'); } catch (e) { }
        });

        // 2. Vẽ mới (Tất cả đều màu vàng mặc định)
        allItems.forEach((item, index) => {
            try {
                // Truyền object rỗng {} vào tham số data.
                // epub.js sẽ tự động sử dụng class mặc định (thường là màu vàng).
                annotations.add(
                    'highlight', 
                    item.cfi_range, 
                    { type: item.type }, // Metadata (không ảnh hưởng hiển thị)
                    undefined, 
                    'highlight-default'
                );
                console.log(`✅ Item #${index} vẽ thành công.`);
            } catch (e) {
                console.error(`❌ Lỗi vẽ ${item.cfi_range}:`, e);
            }
        });
        
        console.groupEnd();
    };

    return {
        book, rendition, isReady, toc,
        initEpub, displayBook, prevPage, nextPage, goToChapter, goToCfi,
        setStyle, resizeBook, drawAnnotations
    };
}