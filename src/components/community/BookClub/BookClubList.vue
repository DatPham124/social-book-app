<script setup lang="ts">
import { ref, onMounted } from "vue"
import axios from "axios"
import { BOOK_SERVICE_URL, BOOKCLUB_IMAGE_SERVER_URL } from "../../../config"
import { useAuth } from "../../../composables/useAuth"
import { getProfile } from "../../../composables/useProfile"

import { useRouter } from "vue-router"

const router = useRouter()

const creatingClub = ref(false)
const clubs = ref<any[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const { userInfo } = useAuth()

function goToClub(clubId: number) {
    router.push(`/bookclub/${clubId}`)
}


async function loadClubs() {
    loading.value = true
    error.value = null

    try {
        const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/`)
        const clubList = res.data

        const clubsWithCreator = await Promise.all(
            clubList.map(async (club: any) => {
                const profile = await getProfile(club.creator_id)
                return {
                    ...club,
                    creator_name: profile?.username,
                }
            })
        )

        clubs.value = clubsWithCreator
    } catch (err: any) {
        console.error("Lỗi khi tải danh sách CLB:", err)
        error.value = "Không thể tải danh sách câu lạc bộ!"
    } finally {
        loading.value = false
    }
}

function startCreate() {
    creatingClub.value = true
}

function handleCancel() {
    creatingClub.value = false
}

function handleCreated(newClub: any) {
    clubs.value.push(newClub)
    creatingClub.value = false
}

onMounted(loadClubs)
</script>


<template>
    <div class="max-w-4xl mx-auto mt-6">
        <div v-if="creatingClub" class="max-w-md mx-auto">
            <BookClubCreate @created="handleCreated" @cancel="handleCancel" />
        </div>

        <div v-else-if="loading" class="text-center text-gray-500 py-10">
            Đang tải...
        </div>

        <div v-else-if="error" class="text-center text-red-500 py-10">
            {{ error }}
        </div>

        <div v-else>
            <div v-for="club in clubs" @click="goToClub(club.id)" :key="club.id"
                class="flex items-center space-x-4 py-4 border-b border-gray-200">
                <div class="w-12 h-12 relative flex-shrink-0">
                    <img v-if="club?.avatar_url" :src="`${BOOKCLUB_IMAGE_SERVER_URL}/${club.avatar_url}`"
                        alt="club avatar"
                        class="w-full h-full object-cover rounded-full border border-gray-200 shadow-sm" />
                    <div v-else
                        class="w-full h-full flex items-center justify-center bg-gray-200 text-gray-500 rounded-full text-sm font-medium">
                        {{ club.name.charAt(0).toUpperCase() }}
                    </div>
                </div>

                <div>
                    <p class="font-semibold text-gray-800">{{ club.name }}</p>
                    <p class="text-sm text-gray-500">Người tạo: {{ club.creator_name }}</p>
                    <p class="text-sm text-gray-500">
                        Ngày tạo:
                        {{ new Date(club.created_at).toLocaleDateString("vi-VN") }}
                        -
                        {{ new Date(club.created_at).toLocaleTimeString("vi-VN", { hour: '2-digit', minute: '2-digit' })
                        }}
                    </p>


                </div>
            </div>
        </div>
    </div>
</template>
