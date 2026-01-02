import { ref } from "vue";
import axios from "axios";
import { debounce } from "lodash";
import { BOOK_SERVICE_URL } from "../config";

export function useBookSearch() {
  const query = ref("");
  const results = ref([]);

  const searchBooks = debounce(async () => {
    if (!query.value) {
      results.value = [];
      return;
    }
    try {
      const res = await axios.get(`${BOOK_SERVICE_URL}books/search?q=${query.value}`);
      results.value = res.data;
    } catch (err) {
      console.error("Error searching books:", err);
      results.value = [];
    }
  }, 300);

  return {
    query,
    results,
    searchBooks,
  };
}
