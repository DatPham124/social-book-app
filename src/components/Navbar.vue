<script>
import { ref } from "vue"
</script>

<template>
    <nav class="bg-white shadow-md">
        <div class=" mx-auto px-4 sm:px-6 lg:px-8">

            <div class="flex justify-between h-16 items-center mx-10">
                <div class="flex space-x-8 item-center">
                    <h1 class="text-2xl font-logo text-yellow-500 item-center">📚 Social Book</h1>

                    <div class="hidden md:flex space-x-6 items-center">
                        <a href="/" class="text-gray-700 hover:text-yellow-500">Trang chủ</a>
                        <a href="/books" class="text-gray-700 hover:text-yellow-500">Sách</a>
                        <a href="/friends" class="text-gray-700 hover:text-yellow-500">Bạn bè</a>
                    </div>


                    <div class="relative">

                        <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                            <font-awesome-icon icon="fa-solid fa-magnifying-glass" />
                        </span>

                        <input type="text" placeholder="Tìm kiếm sách, bạn bè..."
                            class="pl-10 border border-gray-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-yellow-500 w-full">
                    </div>
                </div>
                
                <div>
                    <a href="/profile" class="text-gray-700 hover:text-yellow-500">
                        <img src="../assets/default_avatar.jpg" alt="default avatar"
                            class="w-10 h-10 rounded-full border border-gray-300 hover:ring-2 hover:ring-yellow-500">
                    </a>
                </div>
            </div>
        </div>
    </nav>
</template>
