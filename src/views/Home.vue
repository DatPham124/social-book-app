<script setup>
import Navbar from '../components/Navbar.vue';
import HomeFeed from '../components/HomeFeed.vue';
import { ref } from 'vue';

import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import { ChevronDownIcon } from '@heroicons/vue/20/solid'


const isOpen = ref(false);
</script>

<template>
    <Navbar />


    <div class="w-full max-w-5xl mx-auto m-5 space-y-6">
        <h1 class="text-2xl font-logo text-yellow-400 item-center">Khám phá</h1>

        <div class="bg-white border border-gray-200 rounded-lg shadow-sm ">

            <button @click="isOpen = !isOpen"
                class="focus:outline-none focus:ring-2 focus:ring-yellow-400 w-full flex items-center justify-start p-4 text-left focus:outline-none">

                <svg class="w-5 h-5 text-gray-600 transition-transform duration-300 ease-in-out"
                    :class="{ 'rotate-90': isOpen }" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                    stroke-width="2" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                </svg>

                <span class="ml-3 font-medium text-gray-800">Tùy chọn tìm kiếm</span>
            </button>

            <Transition enter-from-class="opacity-0 -translate-y-2" enter-to-class="opacity-100 translate-y-0"
                enter-active-class="transition ease-out duration-200" leave-from-class="opacity-100 translate-y-0"
                leave-to-class="opacity-0 -translate-y-2" leave-active-class="transition ease-in duration-150">
                <div v-show="isOpen" class="border-t border-gray-200 p-4">
                    <p class="text-gray-600">
                        Bạn có thể thêm các tùy chọn bộ lọc (checkbox, radio button, v.v.) vào đây.
                    </p>

                    <div class="mt-4 space-y-2">
                        <div>
                            <label class="inline-flex items-center">
                                <input type="checkbox" class="form-checkbox h-5 w-5 text-blue-600">
                                <span class="ml-2 text-gray-700">Theo tác giả</span>
                            </label>
                        </div>
                        <div>
                            <label class="inline-flex items-center">
                                <input type="checkbox" class="form-checkbox h-5 w-5 text-blue-600">
                                <span class="ml-2 text-gray-700">Theo thể loại</span>
                            </label>
                        </div>
                    </div>

                </div>
            </Transition>
        </div>


        <Menu as="div" class="relative inline-block">
            <MenuButton
                class="focus:outline-none focus:ring-2 focus:ring-yellow-400 inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-xs inset-ring-1 inset-ring-gray-300 hover:bg-gray-50">
                Cập nhật
                <ChevronDownIcon class="-mr-1 size-5 text-gray-400" aria-hidden="true" />
            </MenuButton>

            <transition enter-active-class="transition ease-out duration-100"
                enter-from-class="transform opacity-0 scale-95" enter-to-class="transform scale-100"
                leave-active-class="transition ease-in duration-75" leave-from-class="transform scale-100"
                leave-to-class="transform opacity-0 scale-95">
                <MenuItems
                    class="absolute left-0-0 z-10 mt-2 w-56 origin-top-left rounded-md bg-white shadow-lg outline-1 outline-black/5">
                    <div class="py-1">
                        <MenuItem v-slot="{ active }">
                        <a href="#"
                            :class="[active ? 'bg-gray-100 text-gray-900 outline-hidden' : 'text-gray-700', 'block px-4 py-2 text-sm']">Account
                            settings</a>
                        </MenuItem>
                        <MenuItem v-slot="{ active }">
                        <a href="#"
                            :class="[active ? 'bg-gray-100 text-gray-900 outline-hidden' : 'text-gray-700', 'block px-4 py-2 text-sm']">Support</a>
                        </MenuItem>
                        <MenuItem v-slot="{ active }">
                        <a href="#"
                            :class="[active ? 'bg-gray-100 text-gray-900 outline-hidden' : 'text-gray-700', 'block px-4 py-2 text-sm']">License</a>
                        </MenuItem>
                        <form method="POST" action="#">
                            <MenuItem v-slot="{ active }">
                            <button type="submit"
                                :class="[active ? 'bg-gray-100 text-gray-900 outline-hidden' : 'text-gray-700', 'block w-full px-4 py-2 text-left text-sm']">Sign
                                out</button>
                            </MenuItem>
                        </form>
                    </div>
                </MenuItems>
            </transition>
        </Menu>

        <HomeFeed />
    </div>
</template>