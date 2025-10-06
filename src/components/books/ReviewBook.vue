<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useBooks } from "../../composables/useBook";
import Navbar from "../layout/Navbar.vue";

const route = useRoute();
const { getBookById } = useBooks();

const bookId = Number(route.params.id);
const book = ref<any>(null);

const review = ref({
  mood: [] as string[],
  pace: "",
  plotType: "",
  characterDev: "",
  loveable: "",
  diversity: "",
  flawsFocus: "",
  rating: 0,
  notes: "",
  themes: "",
  warnings: "",
});

const moods = [
  "phiêu lưu", "hy vọng", "suy ngẫm", "thử thách",
  "thông tin", "thư giãn", "tối tăm", "truyền cảm hứng",
  "buồn", "xúc động", "hài hước", "bí ẩn", "căng thẳng"
];

onMounted(async () => {
  book.value = await getBookById(bookId);
});

function submitReview() {
  console.log("Dữ liệu đánh giá:", review.value);
  alert("Cảm ơn bạn đã gửi đánh giá!");
}
</script>

<template>
  <Navbar />

  <div class="max-w-3xl mx-auto py-10 px-6">
    <h1 class="text-2xl font-bold text-gray-800 mb-2">Thêm đánh giá</h1>
    <p class="mb-6 text-gray-600">
      {{ book?.title ? `${book.title} — ${book.author || "Tác giả không rõ"}` : "Đang tải thông tin sách..." }}
    </p>

    <div class="bg-white border border-gray-200 rounded-xl shadow-md p-6 space-y-6">
      <!-- Mood -->
      <div>
        <h3 class="font-semibold mb-2 text-gray-800">Cuốn sách này phù hợp với tâm trạng:</h3>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
          <label
            v-for="m in moods"
            :key="m"
            class="flex items-center gap-2 cursor-pointer text-gray-700"
          >
            <input
              type="checkbox"
              :value="m"
              v-model="review.mood"
              class="accent-yellow-500"
            />
            <span>{{ m }}</span>
          </label>
        </div>
      </div>

      <!-- Pace -->
      <div>
        <h3 class="font-semibold mb-2 text-gray-800">Tốc độ của sách:</h3>
        <div class="flex gap-4 text-gray-700">
          <label><input type="radio" v-model="review.pace" value="chậm" class="accent-yellow-500" /> Chậm</label>
          <label><input type="radio" v-model="review.pace" value="trung bình" class="accent-yellow-500" /> Trung bình</label>
          <label><input type="radio" v-model="review.pace" value="nhanh" class="accent-yellow-500" /> Nhanh</label>
        </div>
      </div>

      <!-- Select questions -->
      <div class="space-y-4">
        <div>
          <label class="block mb-1 text-gray-700">Cốt truyện thiên về:</label>
          <select v-model="review.plotType" class="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-yellow-400">
            <option value="">-- Chọn --</option>
            <option value="cốt truyện">Cốt truyện</option>
            <option value="nhân vật">Nhân vật</option>
          </select>
        </div>

        <div>
          <label class="block mb-1 text-gray-700">Nhân vật có phát triển mạnh không?</label>
          <select v-model="review.characterDev" class="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-yellow-400">
            <option value="">-- Chọn --</option>
            <option value="có">Có</option>
            <option value="không">Không</option>
          </select>
        </div>

        <div>
          <label class="block mb-1 text-gray-700">Bạn có thấy các nhân vật đáng yêu không?</label>
          <select v-model="review.loveable" class="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-yellow-400">
            <option value="">-- Chọn --</option>
            <option value="có">Có</option>
            <option value="không">Không</option>
          </select>
        </div>

        <div>
          <label class="block mb-1 text-gray-700">Dàn nhân vật có đa dạng không?</label>
          <select v-model="review.diversity" class="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-yellow-400">
            <option value="">-- Chọn --</option>
            <option value="có">Có</option>
            <option value="không">Không</option>
          </select>
        </div>

        <div>
          <label class="block mb-1 text-gray-700">Khiếm khuyết của nhân vật chính có là trọng tâm không?</label>
          <select v-model="review.flawsFocus" class="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-yellow-400">
            <option value="">-- Chọn --</option>
            <option value="có">Có</option>
            <option value="không">Không</option>
          </select>
        </div>
      </div>

      <!-- Rating -->
      <div>
        <label class="block mb-2 font-semibold text-gray-800">Đánh giá sao (0–5):</label>
        <input
          type="number"
          min="0"
          max="5"
          step="0.5"
          v-model.number="review.rating"
          class="w-24 text-center rounded-md border border-gray-300 p-1 focus:ring-2 focus:ring-yellow-400"
        />
      </div>

      <!-- Notes -->
      <div>
        <label class="block mb-2 font-semibold text-gray-800">Ghi chú hoặc cảm nhận:</label>
        <textarea
          v-model="review.notes"
          class="w-full rounded-md border border-gray-300 p-3 focus:ring-2 focus:ring-yellow-400"
          rows="4"
          placeholder="Chia sẻ cảm nhận của bạn về cuốn sách..."
        ></textarea>
      </div>

      <!-- Themes -->
      <div>
        <label class="block mb-2 font-semibold text-gray-800">Chủ đề hoặc thông điệp chính:</label>
        <input
          v-model="review.themes"
          type="text"
          class="w-full rounded-md border border-gray-300 p-2 focus:ring-2 focus:ring-yellow-400"
          placeholder="Ví dụ: tình bạn, khám phá, tự do..."
        />
      </div>

      <!-- Warnings -->
      <div>
        <label class="block mb-2 font-semibold text-gray-800">Cảnh báo nội dung (nếu có):</label>
        <textarea
          v-model="review.warnings"
          class="w-full rounded-md border border-gray-300 p-3 focus:ring-2 focus:ring-yellow-400"
          rows="2"
          placeholder="Ví dụ: bạo lực, trầm cảm..."
        ></textarea>
      </div>

      <!-- Submit -->
      <div class="pt-4 text-right">
        <button
          @click="submitReview"
          class="px-6 py-2 bg-yellow-400 text-gray-900 rounded-md font-semibold hover:bg-yellow-500 transition-colors"
        >
        Lưu đánh giá
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
