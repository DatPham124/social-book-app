import axios from "axios";
import { ref } from "vue";
import { BOOK_SERVICE_URL, REVIEW_SERVICE_URL } from "../config";

export function useBooks() {
  const errorMessage = ref<string | null>(null);

  async function getBookById(book_id: number) {
    try {
      const res = await axios.get(`${BOOK_SERVICE_URL}books/${book_id}`);
      return res.data;
    } catch (error: any) {
      if (axios.isAxiosError(error) && error.response) {
        errorMessage.value = error.response.data.detail || "Lỗi lấy thông tin sách.";
      } else {
        errorMessage.value = "Không thể kết nối đến server.";
      }
      return null;
    }
  }

  async function getBookCategories(bookId: number) {
    try {
      const res = await axios.get(`${BOOK_SERVICE_URL}category/book-category-link/book/${bookId}`);
      return res.data;
    } catch (error) {
      console.error("Lỗi khi lấy liên kết thể loại:", error);
      return [];
    }
  }

  async function getCategory(categoryId: number) {
    try {
      const res = await axios.get(`${BOOK_SERVICE_URL}category/${categoryId}`);
      return res.data;
    } catch (error) {
      console.error("Lỗi khi lấy thể loại:", error);
      return null;
    }
  }

  async function getAuthor(authorId: number) {
    try {
      const res = await axios.get(`${BOOK_SERVICE_URL}author/${authorId}`);
      return res.data;
    } catch (error) {
      console.error("Lỗi khi lấy tác giả :", error);
      return null;
    }
  }

  async function getReadingProgress(userId: number, bookId: number) {
    try {
      const res = await axios.get(`${BOOK_SERVICE_URL}books/reading-progress/${userId}/${bookId}`);
      return res.data;
    } catch (error) {
      // Không log lỗi quá to vì trường hợp chưa đọc bao giờ thì API có thể trả về null hoặc lỗi nhẹ
      // console.error("Lỗi khi lấy tiến độ:", error);
      return null;
    }
  }

  async function getUserBookStatus(userId: number, bookId: number) {
    try {
      const res = await axios.get(`${BOOK_SERVICE_URL}books/status/${userId}/${bookId}`);
      return res.data; 
    } catch (error) {
      console.error("Lỗi khi lấy trạng thái sách:", error);
      return null;
    }
  }

  function formatDate(dateString: string) {
    if (!dateString) return "—";
    return new Date(dateString).toLocaleDateString("vi-VN", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  async function getAverage(book_id: number) {
    try {
      const response = await axios.get(`${REVIEW_SERVICE_URL}review/${book_id}/average-rating`)
       return response.data; 
    }
    catch(error) {
      console.log("Lỗi khi lấy trung bình đánh giá: ", error);
      return null;
    }
  }

  async function getReviewCount(book_id: number) {
    try {
      const response = await axios.get(`${REVIEW_SERVICE_URL}review/${book_id}/review-count`);
      return response.data;
    } catch (error) {
      console.error("Lỗi khi lấy số lượng đánh giá:", error);
      return null;
    }
  }

  // --- HÀM CHÍNH ĐÃ ĐƯỢC CẬP NHẬT ---
  async function fetchBook(bookId: number, userId?: number) {
    try {
      // 1. Lấy chi tiết sách
      const bookRes = await axios.get(`${BOOK_SERVICE_URL}books/${bookId}/details`);
      const bookData = bookRes.data;
      
      if (!bookData) return null;

      // 2. Lấy thông tin phụ (Author, Category, Rating...)
      const author = bookData.authorID ? await getAuthor(bookData.authorID) : null;

      const categoryLinks = await getBookCategories(bookData.id);
      const categoryNames: string[] = [];
      for (const link of categoryLinks) {
        const category = await getCategory(link.category_id);
        if (category?.name) categoryNames.push(category.name);
      }

      // 3. Lấy Tiến độ & Trạng thái (Quan trọng)
      const progress = userId ? await getReadingProgress(userId, bookData.id) : null;
      const userStatus = userId ? await getUserBookStatus(userId, bookData.id) : null;
      
      const averageData = await getAverage(bookData.id);
      const rating = averageData?.average_rating || 0; 
      
      const reviewCountData = await getReviewCount(bookData.id);
      const review_count = reviewCountData?.review_count || 0;

      // 4. Tính toán
      const current_page = progress?.current_page || 0;
      const total_pages = bookData.page_count || 0;
      const progress_percentage =
        total_pages > 0 ? Math.round((current_page / total_pages) * 100) : 0;
      
      // Lấy CFI để đọc Ebook tiếp tục
      const current_cfi = progress?.current_cfi || null;

      // 5. Trả về Object đã gộp
      return {
        ...bookData,
        author: author?.name || "Không xác định",
        categories: categoryNames,
        
        // Thông tin tiến độ
        current_page,
        total_pages,
        progress_percentage,
        current_cfi, // <--- BỔ SUNG CÁI NÀY QUAN TRỌNG
        
        // Thông tin trạng thái
        status: userStatus?.status || "to_read",
        start_date: userStatus?.start_date || null,
        finish_date: userStatus?.finish_date || null,
        is_favorite: userStatus?.is_favorite || false,        
        
        // Thông tin đánh giá
        rating: rating,
        review_count: review_count,
        
        audios: bookData.audios || [] 
      };
    } catch (error) {
      console.error("Lỗi khi tải chi tiết sách:", error);
      return null;
    }
  }

  async function fetchBooksByStatus(userId: number, status: string) {
    try {
      const response = await axios.get(`${BOOK_SERVICE_URL}books/status/book/${userId}`, {
        params: { status },
      });
      return response.data;
    } catch (error: any) {
      console.error("Lỗi khi tải danh sách sách:", error);
      errorMessage.value = error.response?.data?.detail || "Không thể tải danh sách sách";
      return [];
    }
  }
  
  async function toggleFavoriteStatus(userId: number, bookId: number, currentState: boolean) {
    try {
      const res = await axios.put(`${BOOK_SERVICE_URL}books/favorite/update/${bookId}/${userId}`);
      return res.data.is_favorite; 
    } catch (error) {
      console.error("Lỗi khi cập nhật yêu thích:", error);
      return currentState; 
    }
  }

  async function updateReadingDates(userId: number, bookId: number, startDate: string | null, finishDate: string | null) {
    try {
      const payload = {
        start_date: startDate,
        finish_date: finishDate
      };
      const res = await axios.put(`${BOOK_SERVICE_URL}books/status/dates/${userId}/${bookId}`, payload);
      return res.data; 
    } catch (error) {
      console.error("Lỗi khi cập nhật ngày đọc:", error);
      throw error; 
    }
  }

  async function updateReadingProgress(userId: number, bookId: number, currentPage: number) {
    try {
      const payload = {
        current_page: currentPage
      };
      const res = await axios.put(`${BOOK_SERVICE_URL}books/reading-progress/${userId}/${bookId}`, payload);
      return res.data;
    } catch (error) {
      console.error("Lỗi khi cập nhật tiến độ trang:", error);
      throw error;
    }
  }

  return {
    getBookById,
    getBookCategories,
    getCategory,
    getAuthor,
    getReadingProgress,
    getUserBookStatus,
    fetchBook, 
    fetchBooksByStatus,
    formatDate,
    getAverage,
    getReviewCount,
    toggleFavoriteStatus, 
    updateReadingDates,
    updateReadingProgress,
    errorMessage,
  };
}