<script setup>
import Navbar from "../components/layout/Navbar.vue"
import CurentlyReadingBooks from "../components/profile/CurentlyReadingBooks.vue"
import Read from "../components/profile/Read.vue";
import ToReadPile from "../components/profile/ToReadPile.vue";
import DidNotFinish from "../components/profile/DidNotFinish.vue";
import ProfileHeader from "../components/profile/ProfileHeader.vue";
import ProfileReviews from "../components/profile/ProfileReviews.vue"; 
import { useRoute } from "vue-router"
import { computed } from 'vue'

const route = useRoute()
// Lấy ID từ URL (ví dụ /profile/5 -> userID = 5)
const userID = computed(() => route.params.id);
</script>

<template>
    <Navbar />

    <div class="w-full max-w-5xl mx-auto p-4 md:p-6">
        <ProfileHeader :userID="userID" class="mb-6" />

        <div class="grid grid-cols-1 md:grid-cols-[2fr_1fr] gap-6">
            
            <div class="space-y-8">
                <div>
                    <CurentlyReadingBooks :userID="userID" />
                </div>
                <div>
                    <Read :userID="userID" />
                </div>
            </div>
            
            <div class="space-y-6">
                
                <ProfileReviews :userID="userID" />
                
                <DidNotFinish :userID="userID" />

                <div>
                    <ToReadPile :userID="userID" />
                </div>

            </div>
        </div>
    </div>
</template>