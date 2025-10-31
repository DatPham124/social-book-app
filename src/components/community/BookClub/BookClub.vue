<script setup lang="ts">
import { ref } from "vue"
import BookClubList from "../BookClub/BookClubList.vue"
import BookClubForm from "../BookClub/BookClubForm.vue" 

const creatingClub = ref(false)
const createdClub = ref<any>(null)

function startCreate() {
  creatingClub.value = true
}

function handleCancel() {
  creatingClub.value = false
}

function handleSaved(club: any) {
  createdClub.value = club
  creatingClub.value = false
}
</script>

<template>
  <BookClubForm
    v-if="creatingClub"
    mode="create"
    @saved="handleSaved"
    @cancel="handleCancel"
    class="w-full max-w-2xl"
  />

  <div v-else class="w-full max-w-5xl mx-auto">
    <BookClubList :newClub="createdClub" /> 
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
