local mod = RegisterMod("Boss Direction XL", 1)
local GetRoomDistance = require("GetRoomDistance")
local Direction = {
    --[[
        Direction Index
                3
            2       4
        1       O       5
            8       6
                7
        Direction
                -90°
        180°     O      0°
                90°       
    ]]
    [1] = 'Left',       -- (-180,-157.5)° U [157.5,180]°
    [2] = 'Up-Left',    -- [-157.5,-112.5)°
    [3] = 'Up',         -- [-112.5,-67.5)°
    [4] = 'Up-Right',   -- [-67.5,-22.5)°
    [5] = 'Right',      -- [-22.5,22.5)°
    [6] = 'Down-Right', -- [22.5,67.5)°
    [7] = 'Down',       -- [67.5,112.5)°
    [8] = 'Down-Left',  -- [112.5,157.5)°
}
local DoorDirection = {'Left','Up','Right','Down'}
function mod:GetDistAndDirection2Boss()
    local level = Game():GetLevel()
    local stage = level:GetStage()
    assert(stage~=LevelStage.STAGE4_3 and stage~=LevelStage.STAGE8)
    local bossIndex
    local rooms = level:GetRooms()
    if stage ~= LevelStage.STAGE7 then
        for i=1,#rooms do
            local roomDesc = rooms:Get(i-1)
            if roomDesc.Data and roomDesc.Data.Type == RoomType.ROOM_BOSS and i-1 ~= level:GetLastBossRoomListIndex() then
                bossIndex = roomDesc.SafeGridIndex
                break
            end
        end
    else    -- The Void
        for i=1,#rooms do
            local roomDesc = rooms:Get(i-1)
            if roomDesc.Data and roomDesc.Data.Name == 'Delirium' then
                bossIndex = roomDesc.SafeGridIndex
                break
            end
        end
    end

    local x,y = bossIndex%13, bossIndex//13
    local dx,dy = x-6, y-6
    local vectorDegrees = Vector(dx, dy):GetAngleDegrees()+180
    --[[ vectorDegrees
            90°
    
    360°     O      180°
    
            270°    
    ]]
    local directionIndex = ((vectorDegrees-22.5)//45+1)&7
    --[[ directionIndex
            2
        1       3
    0       O       4
        7       5
            6
    ]]
    local direction = Direction[directionIndex+1]

    local minDistance = math.huge
    local currentRoomIndex = level:GetCurrentRoomIndex()
    local bestDirs = {}
    local Neighbor = {-1,-13,1,13}
    for i=0,3 do
        local dirStr = DoorDirection[i+1]
        local dist = GetRoomDistance(currentRoomIndex+Neighbor[i+1], bossIndex)
        if 0 < dist and dist < minDistance then
            minDistance = dist
            bestDirs = {[dirStr]=true}
        elseif dist == minDistance then
            bestDirs[dirStr] = true
        end
    end

    return bestDirs, direction
end


local Stages = {
    '1','1a','1b','1c','1d',
    -- '2','2a','2b','2c','2d',
    '3','3a','3b','3c','3d',
    -- '4','4a','4b','4c','4d',
    '5','5a','5b','5c','5d',
    -- '6','6a','6b','6c','6d',
    '7','7a','7b','7c',
    -- '8','8a','8b','8c',
    -- '9',
    -- '10','10a',
    -- '11','11a',
    -- '12',
    -- '13','13a'
}

local data = {}
local json = require("json")
function mod:Save()
    mod:SaveData(json.encode(data))
end
function mod:Load()
    if mod:HasData() then
        data = json.decode(mod:LoadData()) or data
    end
end
function BDXLResetData()
    data = {}
    mod:Save()
end

local firstRun = true
local index=1
mod:AddCallback(ModCallbacks.MC_POST_UPDATE, function(self)
    self:Load()
    if firstRun then
        firstRun = false
        Isaac.ExecuteCommand("restart")
        return
    end
    local key = Stages[index]
    Isaac.ExecuteCommand("stage "..key)
    data[key] = data[key] or {}
    local stageData= data[key]
    stageData.Total = (stageData.Total or 0) + 1
    stageData.Directions = stageData.Directions or {}
    stageData.Doors = stageData.Doors or {}
    
    local bestDirs,dir = self:GetDistAndDirection2Boss()
    stageData.Directions[dir] = (stageData.Directions[dir] or 0) + 1
    for dirStr,_ in pairs(bestDirs) do
        stageData.Doors[dirStr] = (stageData.Doors[dirStr] or 0) + 1
    end

    index = index%#Stages + 1
    if index == 1 then
        Isaac.ExecuteCommand("restart")
    end
    self:Save()
end)

mod:AddCallback(ModCallbacks.MC_POST_CURSE_EVAL, function(self, curses)
    return LevelCurse.CURSE_OF_LABYRINTH | curses
end)

mod:AddCallback(ModCallbacks.MC_POST_RENDER, function(self)
    local pos = Vector(30, 20)
    for k,v in ipairs(Stages) do
        local text = string.format("%3s: ", v)
        data[v] = data[v] or {}
        local total = data[v].Total or 0
        if total > 0 then
            if Input.IsMouseBtnPressed(Mouse.MOUSE_BUTTON_RIGHT) then
                for dir,str in ipairs(Direction) do
                    local count = data[v].Directions and data[v].Directions[str] or 0
                    text = text..string.format("%s=%5.2f%% ", str, count*100/total)
                end
            else
                for _,dir in ipairs(DoorDirection) do
                    local count = data[v].Doors and data[v].Doors[dir] or 0
                    text = text..string.format("%s=%5.2f%% ", dir, count*100/total)
                end
            end
            text = text.."| Total="..total
            local renderSize = 0.5
            Isaac.RenderScaledText(text, pos.X, pos.Y, renderSize, renderSize, 1,1,1,1)
            pos.Y = pos.Y + 10 * renderSize
        end
    end
end)

mod:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, function(self, isContinued)
    Options.PauseOnFocusLost = false
    Game():GetHUD():SetVisible(false)
    Isaac.GetPlayer().Visible = false
end)

mod:AddCallback(ModCallbacks.MC_PRE_MOD_UNLOAD, function(self)
    Options.PauseOnFocusLost = true
end)