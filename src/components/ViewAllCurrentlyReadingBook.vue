<script setup>
import Navbar from "../components/Navbar.vue";

</script>

<template>

    <Navbar />

    <div class="max-w-5xl mx-auto p-6">

        <!-- Header -->
        <div class="flex items-center justify-between mb-4">

            <h1 class="text-2xl font-logo text-yellow-400 item-center">Sách đang đọc</h1>
            <router-link to="" class="px-4 py-1 rounded-md border bg-white hover:bg-yellow-200 text-sm">Xem nhật
                ký</router-link>
        </div>

        <p class="text-gray-500 text-sm mb-6">2 sách</p>

        <div class="flex border rounded-md shadow-sm mb-4">
  <!-- Cover -->
  <div class="w-32 h-48 bg-gray-200">
    <!-- Ảnh bìa sẽ để ở đây -->
  </div>

  <!-- Info -->
  <div class="flex-1 p-4 relative">
    <!-- Track progress -->
    <button
      class="absolute top-4 right-4 px-3 py-1 rounded-md border bg-gray-100 text-sm hover:bg-gray-200"
    >
      Track progress
    </button>

    <!-- Title & author -->
    <h3 class="font-bold text-lg">Engines of Chaos</h3>
    <p class="text-gray-600 text-sm">R.S. Ford</p>
    <p class="text-gray-500 text-sm mb-2">608 pages • paperback • 2023</p>

    <!-- Tags -->
    <div class="flex flex-wrap gap-2 mb-2">
      <span class="px-2 py-1 bg-pink-100 text-pink-700 rounded-md text-xs">
        adventurous
      </span>
      <span class="px-2 py-1 bg-green-100 text-green-700 rounded-md text-xs">
        fantasy
      </span>
      <!-- thêm tag khác -->
    </div>

    <!-- Started date -->
    <p class="text-sm text-gray-500 mb-2">Started Sep 26, 2025</p>

    <!-- Status + buttons -->
    <div class="flex items-center gap-2">
      <span class="px-3 py-1 bg-green-100 text-green-700 rounded-md text-sm">
        currently reading
      </span>
      <button class="text-sm text-gray-600 hover:underline">
        mark as "finished"
      </button>
    </div>
  </div>
</div>

    </div>




</template>