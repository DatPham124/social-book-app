<script setup>
import Footer from './components/Footer.vue';
</script>

<template>
  <div class="flex flex-col min-h-screen bg-[#F3F4F6]">
    <main class="flex-grow">
      <router-view />
    </main>
    <Footer />
  </div>

</template>
