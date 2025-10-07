// Trong useBooks.ts
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
      const res = await axios.get(`${BOOK_SERVICE_URL}authors/${authorId}`);
      return res.data;
    } catch (error) {
      console.error("Lỗi khi lấy tác giả:", error);
      return null;
    }
  }

  async function getReadingProgress(userId: number, bookId: number) {
    try {
      const res = await axios.get(`${BOOK_SERVICE_URL}books/reading-progress/${userId}/${bookId}`);
      return res.data;
    } catch (error) {
      console.error("Lỗi khi lấy tiến độ:", error);
      return null;
    }
  }

  async function getUserBookStatus(userId: number, bookId: number) {
    try {
      const res = await axios.get(`${BOOK_SERVICE_URL}books/status/${userId}/${bookId}`);
      return res.data; // { status: "currently_reading", start_date: ... }
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


  async function fetchBook(bookId: number, userId?: number) {
    try {
      const bookData = await getBookById(bookId);
      if (!bookData) return null;

      const author = bookData.authorID ? await getAuthor(bookData.authorID) : null;

      const categoryLinks = await getBookCategories(bookData.id);
      const categoryNames: string[] = [];
      for (const link of categoryLinks) {
        const category = await getCategory(link.category_id);
        if (category?.name) categoryNames.push(category.name);
      }

      const progress = userId ? await getReadingProgress(userId, bookData.id) : null;

      const userStatus = userId ? await getUserBookStatus(userId, bookData.id) : null;

      const averageRating = await getAverage(bookData.id)

      const reviewCount = await getReviewCount(bookData.id)

      const current_page = progress?.current_page || 0;
      const total_pages = bookData.page_count || 0;
      const progress_percentage =
        total_pages > 0 ? Math.round((current_page / total_pages) * 100) : 0;

      return {
        ...bookData,
        author: author?.name || "Không xác định",
        categories: categoryNames,
        current_page,
        total_pages,
        progress_percentage,
        newPage: current_page,
        status: userStatus?.status || "to_read", // 👈 trạng thái thật của user
        start_date: userStatus?.start_date || null,
        rating: 4.5,
        review_count: reviewCount?.review_count || 0,
        warnings: [],
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
    errorMessage,
  };
}
