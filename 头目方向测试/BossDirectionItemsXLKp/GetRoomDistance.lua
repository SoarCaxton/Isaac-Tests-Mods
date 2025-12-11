local RoomShape_Slot2IndexOffset = {
    [RoomShape.ROOMSHAPE_1x1]={
        [DoorSlot.LEFT0] = {x=-1, y=0},
        [DoorSlot.UP0] = {x=0, y=-1},
        [DoorSlot.RIGHT0] = {x=1, y=0},
        [DoorSlot.DOWN0] = {x=0, y=1},
    },
    [RoomShape.ROOMSHAPE_IH]={
        [DoorSlot.LEFT0] = {x=-1, y=0},
        [DoorSlot.RIGHT0] = {x=1, y=0},
    },
    [RoomShape.ROOMSHAPE_IV]={
        [DoorSlot.UP0] = {x=0, y=-1},
        [DoorSlot.DOWN0] = {x=0, y=1},
    },
    [RoomShape.ROOMSHAPE_1x2]={
        [DoorSlot.LEFT0] = {x=-1, y=0},
        [DoorSlot.UP0] = {x=0, y=-1},
        [DoorSlot.RIGHT0] = {x=1, y=0},
        [DoorSlot.DOWN0] = {x=0, y=2},
        [DoorSlot.LEFT1] = {x=-1, y=1},
        [DoorSlot.RIGHT1] = {x=1, y=1},
    },
    [RoomShape.ROOMSHAPE_IIV]={
        [DoorSlot.UP0] = {x=0, y=-1},
        [DoorSlot.DOWN0] = {x=0, y=2},
    },
    [RoomShape.ROOMSHAPE_2x1]={
        [DoorSlot.LEFT0] = {x=-1, y=0},
        [DoorSlot.UP0] = {x=0, y=-1},
        [DoorSlot.RIGHT0] = {x=2, y=0},
        [DoorSlot.DOWN0] = {x=0, y=1},
        [DoorSlot.UP1] = {x=1, y=-1},
        [DoorSlot.DOWN1] = {x=1, y=1}
    },
    [RoomShape.ROOMSHAPE_IIH]={
        [DoorSlot.LEFT0] = {x=-1, y=0},
        [DoorSlot.RIGHT0] = {x=2, y=0},
    },
    [RoomShape.ROOMSHAPE_2x2]={
        [DoorSlot.LEFT0] = {x=-1, y=0},
        [DoorSlot.UP0] = {x=0, y=-1},
        [DoorSlot.RIGHT0] = {x=2, y=0},
        [DoorSlot.DOWN0] = {x=0, y=2},
        [DoorSlot.LEFT1] = {x=-1, y=1},
        [DoorSlot.UP1] = {x=1, y=-1},
        [DoorSlot.RIGHT1] = {x=2, y=1},
        [DoorSlot.DOWN1] = {x=1, y=2}
    },
    [RoomShape.ROOMSHAPE_LTL]={
        [DoorSlot.LEFT0] = {x=-1, y=0},
        [DoorSlot.UP0] = {x=-1, y=0},
        [DoorSlot.RIGHT0] = {x=1, y=0},
        [DoorSlot.DOWN0] = {x=-1, y=2},
        [DoorSlot.LEFT1] = {x=-2, y=1},
        [DoorSlot.UP1] = {x=0, y=-1},
        [DoorSlot.RIGHT1] = {x=1, y=1},
        [DoorSlot.DOWN1] = {x=0, y=2}
    },
    [RoomShape.ROOMSHAPE_LTR]={
        [DoorSlot.LEFT0] = {x=-1, y=0},
        [DoorSlot.UP0] = {x=0, y=-1},
        [DoorSlot.RIGHT0] = {x=1, y=0},
        [DoorSlot.DOWN0] = {x=0, y=2},
        [DoorSlot.LEFT1] = {x=-1, y=1},
        [DoorSlot.UP1] = {x=1, y=0},
        [DoorSlot.RIGHT1] = {x=2, y=1},
        [DoorSlot.DOWN1] = {x=1, y=2}
    },
    [RoomShape.ROOMSHAPE_LBL]={
        [DoorSlot.LEFT0] = {x=-1, y=0},
        [DoorSlot.UP0] = {x=0, y=-1},
        [DoorSlot.RIGHT0] = {x=2, y=0},
        [DoorSlot.DOWN0] = {x=0, y=1},
        [DoorSlot.LEFT1] = {x=0, y=1},
        [DoorSlot.UP1] = {x=1, y=-1},
        [DoorSlot.RIGHT1] = {x=2, y=1},
        [DoorSlot.DOWN1] = {x=1, y=2}
    },
    [RoomShape.ROOMSHAPE_LBR]={
        [DoorSlot.LEFT0] = {x=-1, y=0},
        [DoorSlot.UP0] = {x=0, y=-1},
        [DoorSlot.RIGHT0] = {x=2, y=0},
        [DoorSlot.DOWN0] = {x=0, y=2},
        [DoorSlot.LEFT1] = {x=-1, y=1},
        [DoorSlot.UP1] = {x=1, y=-1},
        [DoorSlot.RIGHT1] = {x=1, y=1},
        [DoorSlot.DOWN1] = {x=1, y=1}
    }
}

local function Room_Slot2Room(room, doorSlot, dimension)
    local safeGridIndex, roomShape = room.SafeGridIndex, room.Data.Shape
    local x,y = safeGridIndex % 13, safeGridIndex // 13
    local offset = RoomShape_Slot2IndexOffset[roomShape][doorSlot]
    if offset then
        x, y = x + offset.x, y + offset.y
        if x >= 0 and x < 13 and y >= 0 and y < 13 then
            local targetRoom = Game():GetLevel():GetRoomByIdx(y * 13 + x, dimension)
            return targetRoom.Data and targetRoom
        end
    end
end

local function GetRoomDistance(safegridindexA, safegridindexB, dimension)
    local level = Game():GetLevel()
    local roomA = level:GetRoomByIdx(safegridindexA, dimension)
    local roomB = level:GetRoomByIdx(safegridindexB, dimension)
    if not (roomA.Data and roomB.Data) then
        return -1
    end

    local visited = {}
    local queue = {}
    table.insert(queue, {room=roomA, distance=0})
    visited[roomA.SafeGridIndex] = true

    while #queue > 0 do
        local current = table.remove(queue, 1)
        if current.room.SafeGridIndex == safegridindexB then
            return current.distance
        end

        for doorSlot=0,7 do
            if 1 << doorSlot & current.room.Data.Doors > 0 then
                local neighborRoom = Room_Slot2Room(current.room, doorSlot, dimension)
                if neighborRoom and not visited[neighborRoom.SafeGridIndex] then
                    if neighborRoom then
                        visited[neighborRoom.SafeGridIndex] = true
                        table.insert(queue, {room=neighborRoom, distance=current.distance + 1})
                    end
                end
            end
        end
    end

    return -1
end

return GetRoomDistance