<script setup lang="ts">
import BookList from '../books/BookList.vue'
import Navbar from '../layout/Navbar.vue';
</script>

<template>
  <Navbar />
  <BookList status="currently_reading" title="Sách đang đọc" />
</template>