<script setup lang="ts">
import BookList from '../books/BookList.vue'
import Navbar from '../layout/Navbar.vue';
</script>

<template>
  <Navbar />
  <BookList status="read" title="Sách đã đọc" />
</template>