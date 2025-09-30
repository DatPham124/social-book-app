<script setup>
import Navbar from "../components/Navbar.vue"
import CurentlyReadingBooks from "../components/CurentlyReadingBooks.vue"
import Read from "../components/Read.vue";
import ToReadPile from "../components/ToReadPile.vue";
import ProfileHeader from "../components/ProfileHeader.vue";
</script>

<template>

    <Navbar />

    <div class="w-full max-w-6xl mx-auto p-6 space-y-8">
        <ProfileHeader />

        <div class="grid grid-cols-[2fr_1fr] gap-6">

            
            <div class="space-y-6">
                <CurentlyReadingBooks />

                <Read />
            </div>

            <div class="space-y-6">
                <div class="bg-white p-6 rounded-lg shadow border">
                    <p class="text-gray-700 mb-2">
                        Mainly reads <span class="text-teal-700 font-medium">nonfiction</span> books that are
                        <span class="text-teal-700 font-medium">reflective, informative, and inspiring.</span>
                    </p>
                    <p class="text-gray-700">
                        Typically chooses <span class="text-teal-700 font-medium">slow-paced</span> books that are
                        <span class="text-teal-700 font-medium">&lt;300 pages</span> long.
                    </p>
                    <div class="mt-4 flex space-x-3">
                        <button class="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 text-sm">Stats</button>
                        <button class="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 text-sm">Reading
                            Preferences</button>
                    </div>
                </div>

                <ToReadPile />


            </div>
        </div>
    </div>
</template>
