<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { REVIEW_SERVICE_URL } from "../../config";
import { useBooks } from "../../composables/useBook";
import Navbar from "../../components/layout/Navbar.vue";
import { useAuth } from "../../composables/useAuth";
import axios from "axios";
import { useRouter } from "vue-router";
const router = useRouter();

const { userInfo } = useAuth();
const route = useRoute();
const { getBookById } = useBooks();

const bookId = Number(route.params.id);
const book = ref<any>(null);
const review_data = ref<any>(null);

const review = ref({
  rating: 0,
  content: "",
});

async function deleteReview() {
  if (!review_data.value) {
    alert("Không có đánh giá nào để xóa.");
    return;
  }

  const confirmDelete = confirm("Bạn có chắc chắn muốn xóa đánh giá này không?");
  if (!confirmDelete) return;

  try {
    await axios.delete(`${REVIEW_SERVICE_URL}review/delete/${review_data.value.id}`);
    alert("Đã xóa đánh giá thành công!");
    review_data.value = null;
    review.value.rating = 0;
    review.value.content = "";
  } catch (error) {
    console.error("Lỗi khi xóa đánh giá:", error);
    alert("Không thể xóa đánh giá, vui lòng thử lại sau.");
  } finally {
    router.push(`/book/${bookId}`);
  }
}



async function getReview(userId: number, bookId: number) {
  try {
    const response = await axios.get(`${REVIEW_SERVICE_URL}review/${bookId}/${userId}`);
    if (response.data) {
      review_data.value = response.data;
      review.value.rating = response.data.rating;
      review.value.content = response.data.content;
      console.log("Đã tải review cũ:", response.data);
    }
  } catch (error: any) {
    if (error.response?.status === 404) {
      console.log("Người dùng chưa có đánh giá cho cuốn này.");
    } else {
      console.error("Lỗi khi tải review:", error);
    }
  } 
}


async function addReview(userId: number, bookId: number, rating: number, content: string) {
  try {
    const response = await axios.post(`${REVIEW_SERVICE_URL}review/add`, null, {
      params: {
        user_id: userId,
        book_id: bookId,
        rating: rating,
        content: content,
      },
    });
    console.log("Thêm đánh giá thành công:", response.data);
    return response.data;

  } catch (error) {
    console.error("Có lỗi khi thêm bình luận:", error);

    throw error;
  } 
}


async function updateReview(reviewId: number, rating: number, content: string) {
  try {
    const response = await axios.put(`${REVIEW_SERVICE_URL}review/update/${reviewId}`, {
      rating: rating,
      content: content,
    });
    console.log("Cập nhật đánh giá thành công:", response.data);
    return response.data;
  } catch (error) {
    console.error("Lỗi khi cập nhật review:", error);
    throw error;
  }
}


async function submitReview() {
  if (!userInfo.value) {
    alert("Vui lòng đăng nhập trước khi đánh giá sách!");
    return;
  }

  if (review.value.rating <= 0) {
    alert("Vui lòng chọn điểm đánh giá (0–5).");
    return;
  }

  try {
    if (review_data.value) {
      await updateReview(review_data.value.id, review.value.rating, review.value.content);
      alert("Cập nhật đánh giá thành công!");
    } else {
      await addReview(userInfo.value.user_id, bookId, review.value.rating, review.value.content);
      alert("Cảm ơn bạn đã gửi đánh giá!");
    }

    await getReview(userInfo.value.user_id, bookId);
  } catch (error) {
    alert("Không thể gửi đánh giá, vui lòng thử lại sau.");
  } 
}


onMounted(async () => {
  book.value = await getBookById(bookId);
  if (userInfo.value) {
    await getReview(userInfo.value.user_id, bookId);
  }
});
</script>

<template>
  <Navbar />

  <div class="max-w-3xl mx-auto py-10 px-6">
    <h1 class="text-2xl font-bold text-gray-800 mb-2">
      {{ review_data ? "Cập nhật đánh giá" : "Thêm đánh giá" }}
    </h1>
    <p class="mb-6 text-gray-600">
      {{ book?.title ? `${book.title} — ${book.author || "Tác giả không rõ"}` : "Đang tải thông tin sách..." }}
    </p>

    <div class="bg-white border border-gray-200 rounded-xl shadow-md p-6 space-y-6">
      <div>
        <label class="block mb-2 font-semibold text-gray-800">Đánh giá sao (0–5):</label>
        <input type="number" min="0" max="5" step="0.5" v-model.number="review.rating"
          class="w-24 text-center rounded-md border border-gray-300 p-1 focus:ring-2 focus:ring-yellow-400" />
      </div>

      <div>
        <label class="block mb-2 font-semibold text-gray-800">Cảm nhận hoặc ghi chú:</label>
        <textarea v-model="review.content"
          class="w-full rounded-md border border-gray-300 p-3 focus:ring-2 focus:ring-yellow-400" rows="4"
          placeholder="Chia sẻ cảm nhận của bạn về cuốn sách..."></textarea>
      </div>

      <div class="pt-4">
        <button @click="submitReview"
          class="px-6 py-2 bg-yellow-400 text-gray-900 rounded-md font-semibold hover:bg-yellow-500 transition-colors">
          {{ review_data ? "Cập nhật đánh giá" : "Lưu đánh giá" }}
        </button>
        <!-- Đường kẻ ngang -->
        <hr class="my-6 border-gray-300" />

        <!-- Nút xóa bình luận -->
        <button v-if="review_data" @click="deleteReview"
          class="px-6 py-2 bg-red-500 text-white rounded-md font-semibold hover:bg-red-600 transition-colors">
          Xóa đánh giá
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
select,
input[type="number"],
textarea {
  outline: none;
  transition: all 0.2s;
}
</style>
