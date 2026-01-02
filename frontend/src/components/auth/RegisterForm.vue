<script setup>
import { ref, watch, onBeforeUnmount } from "vue"
import { useRouter } from "vue-router"
import axios from "axios"
import { USER_SERVICE_URL } from "../../config.ts"

const username = ref("")
const email = ref("")
const password = ref("")
const confirmPassword = ref("")
const isLoading = ref(false)
const errorMessages = ref("")
const router = useRouter()
const showPopup = ref(false)
const count = ref(5)
let interval = null

async function register() {
  errorMessages.value = "" // reset lỗi trước khi submit
  isLoading.value = true

  try {
    if (password.value !== confirmPassword.value) {
      errorMessages.value = "Mật khẩu không khớp"
      return
    }

    await axios.post(`${USER_SERVICE_URL}users/register`, {
      username: username.value,
      email: email.value,
      password: password.value,
    })

    showPopup.value = true
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      errorMessages.value = error.response.data.detail || "Đăng ký thất bại"
    } else {
      errorMessages.value = "Không thể kết nối đến server"
    }
  } finally {
    isLoading.value = false
  }
}

watch(showPopup, (val) => {
  if (val) {
    count.value = 5
    interval = setInterval(() => {
      count.value--
      if (count.value <= 0) {
        closePopup()
      }
    }, 1000)
  } else {
    if (interval) {
      clearInterval(interval)
      interval = null
    }
  }
})

function closePopup() {
  if (interval) {
    clearInterval(interval)
    interval = null
  }
  router.push("/login")
}

onBeforeUnmount(() => {
  if (interval) clearInterval(interval)
})
</script>

<template>
  <div class="flex items-center justify-center mt-10">
    <form
      class="bg-white p-8 rounded-2xl shadow-lg w-full max-w-md space-y-6"
      @submit.prevent="register"
    >
      <h1 class="text-4xl font-logo text-yellow-500 text-center">📚 Social Book</h1>
      <h2 class="text-2xl font-semibold text-center">Đăng ký</h2>

      <div>
        <label for="username" class="block text-sm font-medium text-gray-700"
          >Tên đăng nhập</label
        >
        <input
          v-model="username"
          id="username"
          type="text"
          placeholder="Nhập tên của bạn"
          class="mt-2 w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
        />
      </div>

      <div>
        <label for="email" class="block text-sm font-medium text-gray-700">Email</label>
        <input
          v-model="email"
          id="email"
          type="email"
          placeholder="Nhập email của bạn"
          class="mt-2 w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
        />
      </div>

      <div>
        <label for="password" class="block text-sm font-medium text-gray-700"
          >Mật khẩu</label
        >
        <input
          v-model="password"
          id="password"
          type="password"
          placeholder="Nhập mật khẩu"
          class="mt-2 w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
        />
      </div>

      <div>
        <label
          for="confirmPassword"
          class="block text-sm font-medium text-gray-700"
          >Nhập lại mật khẩu</label
        >
        <input
          v-model="confirmPassword"
          id="confirmPassword"
          type="password"
          placeholder="Xác nhận mật khẩu"
          class="mt-2 w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
        />
      </div>

      <button
        :disabled="isLoading"
        type="submit"
        class="w-full py-3 rounded-lg bg-yellow-400 text-gray-900 font-semibold hover:bg-yellow-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span v-if="isLoading">⏳ Đang xử lý...</span>
        <span v-else>Tạo tài khoản</span>
      </button>

      <p v-if="errorMessages" class="text-red-500 text-sm">{{ errorMessages }}</p>

      <p class="text-sm text-gray-600 text-center">
        Đã có tài khoản?
        <router-link to="/login" class="text-blue-500 hover:underline"
          >Đăng nhập</router-link
        >
      </p>
    </form>

    <!-- Popup -->
    <div v-if="showPopup" class="fixed flex items-center justify-center z-50">
      <div class="fixed inset-0 bg-white/50 backdrop-blur-sm"></div>

      <div
        class="relative bg-white p-6 rounded-3xl shadow-2xl text-center w-80 z-10"
      >
        <h3 class="text-xl font-semibold text-green-600">🎉 Đăng ký thành công!</h3>
        <p class="mt-2 text-gray-600">Chúc mừng bạn đã tạo tài khoản mới.</p>
        <p class="mt-2 text-gray-500 text-sm">
          Tự động chuyển trong {{ count }} giây...
        </p>
        <button
          @click="closePopup"
          class="mt-4 px-4 py-2 bg-yellow-400 rounded-lg hover:bg-yellow-500"
        >
          Về trang đăng nhập ngay
        </button>
      </div>
    </div>
  </div>
</template>
