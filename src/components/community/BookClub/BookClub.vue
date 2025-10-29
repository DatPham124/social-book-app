<script setup lang="ts">
import { ref } from "vue"
import BookClubList from "../BookClub/BookClubList.vue"
import BookClubCreate from "../BookClub/BookClubCreate.vue"

const creatingClub = ref(false)
const createdClub = ref<any>(null)

function startCreate() {
  creatingClub.value = true
}

function handleCancel() {
  creatingClub.value = false
}

function handleCreated(club: any) {
  createdClub.value = club
  creatingClub.value = false
}
</script>

<template>

  <!-- Form tạo CLB -->
  <BookClubCreate v-if="creatingClub" @created="handleCreated" @cancel="handleCancel" class="w-full max-w-2xl" />
<div v-else class="w-full max-w-5xl mx-auto">

  <BookClubList />

  <div class="flex justify-end mt-6">
    <button
      @click="startCreate"
      class="bg-yellow-400 hover:bg-yellow-500 text-black font-semibold px-4 py-2 rounded-md transition"
    >
      + Tạo mới
    </button>
  </div>

</div>


</template>
