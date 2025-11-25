import { ref, onUnmounted } from 'vue';
import { 
    doc, 
    onSnapshot, 
    setDoc, 
    serverTimestamp 
} from 'firebase/firestore'; 

// Import db từ file chung (Quan trọng!)
import { db } from '../firebase'; 

export function useAudioSync() {
    const remoteCommand = ref<{
        action: 'play' | 'pause' | 'seek' | 'change_chapter';
        payload: any;
        updatedBy?: number | string;
        timestamp?: any;
    } | null>(null);

    let unsubscribe: (() => void) | null = null;

    // 1. Tham gia phòng
    const joinRoom = (roomId: string, currentUserId: number | string) => {
        leaveRoom();

        // Lưu trạng thái player vào chung collection 'rooms'
        // Path: rooms/{roomId}/player/state
        const docRef = doc(db, 'rooms', roomId, 'player', 'state');

        unsubscribe = onSnapshot(docRef, (docSnap) => {
            if (docSnap.exists()) {
                const data = docSnap.data();
                
                // Bỏ qua nếu là lệnh do chính mình gửi
                if (String(data.updatedBy) === String(currentUserId)) return;

                console.log("🔥 Sync nhận lệnh:", data.action);
                
                remoteCommand.value = {
                    action: data.action,
                    payload: data.payload,
                    updatedBy: data.updatedBy,
                    timestamp: data.timestamp
                };
            }
        });
    };

    // 2. Rời phòng
    const leaveRoom = () => {
        if (unsubscribe) {
            unsubscribe();
            unsubscribe = null;
        }
    };

    // 3. Gửi lệnh
    const sendControl = async (roomId: string, action: string, payload: any, userId: number | string) => {
        const docRef = doc(db, 'rooms', roomId, 'player', 'state');
        
        try {
            await setDoc(docRef, {
                action,
                payload,
                updatedBy: userId,
                timestamp: serverTimestamp() 
            }, { merge: true });
        } catch (e) {
            console.error("Lỗi gửi lệnh sync:", e);
        }
    };

    onUnmounted(() => {
        leaveRoom();
    });

    return {
        remoteCommand,
        joinRoom,
        leaveRoom,
        sendControl
    };
}