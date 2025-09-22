<script setup lang="ts">
import LoginForm from '../components/LoginForm.vue';
</script>

<template>
  <div class="relative">
    <div class="w-full h-65 bg-yellow-400 absolute z-0 mt-19"></div>

    <div class="relative mx-auto w-5xl z-10">
      <h1 class=" left-2 text-3xl font-logo z-10 p-5">📚 Social Book</h1>

      <img src="../assets/login_2.png" alt="Books Background" class="h-65 relative" />


      <div class="flex justify-between">
        <img src="../assets/login_3.png" alt="Books Background" class="h-80 relative mt-10 flex-1" />

        <div class="flex-1 mt-25">
          <p class="text-5xl font-bold">Connect with friends.</p>
          <p class="text-5xl font-bold mt-3">Share your world.</p>
          <p class="text-2xl mt-5">Join millions of users on Social Book today</p>

        </div>
      </div>
      <div class="absolute w-[300px] top-0 right-0 rounded-xl shadow-lg p-6 mt-6 bg-white">
        <h2 class="text-xl font-serif font-bold mb-4 text-center">Login</h2>

        <LoginForm />

        <p class="text-sm text-gray-600 mt-4 text-center">
          Don't have an account?
          <a href="/register" class="text-blue-500 hover:underline">Register</a>
        </p>
      </div>

    </div>
  </div>
</template>