local mod = RegisterMod("Boss Direction2", 1)
local GetRoomDistance = require("GetRoomDistance")

function mod:GetDist2Boss(indexOffset)
    local level = Game():GetLevel()
    local stage = level:GetStage()
    assert(stage~=LevelStage.STAGE4_3 and stage~=LevelStage.STAGE8)
    local bossIndex
    local rooms = level:GetRooms()
    if stage ~= LevelStage.STAGE7 then
        for i=1,#rooms do
            local roomDesc = rooms:Get(i-1)
            if roomDesc.Data and roomDesc.Data.Type == RoomType.ROOM_BOSS then
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
    return GetRoomDistance(level:GetCurrentRoomIndex()+indexOffset, bossIndex)
end

local Stages = {
    '1','1a','1b','1c','1d',
    '2','2a','2b','2c','2d',
    '3','3a','3b','3c','3d',
    '4','4a','4b','4c','4d',
    '5','5a','5b','5c','5d',
    '6','6a','6b','6c','6d',
    '7','7a','7b','7c',
    '8','8a','8b','8c',
    -- '9',
    '10','10a',
    '11','11a',
    '12',
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
function BD2ResetData()
    data = {}
    mod:Save()
end

local firstRun = true
local index=1
local Direction = {'Left','Up','Right','Down'}
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
    local minDistance = math.huge
    local bestDirs = {}
    local Neighbor = {-1,-13,1,13}
    for i=0,3 do
        local dirStr = Direction[i+1]
        local dist = self:GetDist2Boss(Neighbor[i+1])
        if 0 < dist and dist < minDistance then
            minDistance = dist
            bestDirs = {[dirStr]=true}
        elseif dist == minDistance then
            bestDirs[dirStr] = true
        end
    end
    for dirStr,_ in pairs(bestDirs) do
        stageData[dirStr] = (stageData[dirStr] or 0) + 1
    end

    index = index%#Stages + 1
    if index == 1 then
        Isaac.ExecuteCommand("restart")
    end
    self:Save()
end)

mod:AddCallback(ModCallbacks.MC_POST_CURSE_EVAL, function(self, curses)
    return ~LevelCurse.CURSE_OF_LABYRINTH & curses
end)

mod:AddCallback(ModCallbacks.MC_POST_RENDER, function(self)
    local pos = Vector(40, 20)
    for k,v in ipairs(Stages) do
        local text = string.format("%3s: ", v)
        local total = data[v] and data[v].Total or 0
        if total > 0 then
            for _,dir in ipairs(Direction) do
                local count = data[v][dir] or 0
                text = text..string.format("%s=%5.2f%% ", dir, count*100/total)
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