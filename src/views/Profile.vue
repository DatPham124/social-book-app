<script setup>
import Navbar from "../components/layout/Navbar.vue"
import CurentlyReadingBooks from "../components/books/CurentlyReadingBooks.vue"
import Read from "../components/books/Read.vue";
import ToReadPile from "../components/books/ToReadPile.vue";
import ProfileHeader from "../components/profile/ProfileHeader.vue";
import {useRoute} from "vue-router"

const route = useRoute()

const userID = route.params.id;
</script>

<template>

    <Navbar />

    <div class="w-full max-w-5xl mx-auto">
        <ProfileHeader :userID = "userID"/>

        <div class="grid grid-cols-[2fr_1fr] gap-6">


            <CurentlyReadingBooks class="h-[325px] flex items-center justify-center" />

            <div class="bg-white p-6 rounded-lg shadow border">

            </div>

            <Read class="h-[325px] flex items-center justify-center" />

            <ToReadPile class="h-[325px]" />
        </div>
    </div>
</template>
