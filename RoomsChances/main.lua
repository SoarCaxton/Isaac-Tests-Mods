local mod = RegisterMod("Rooms Chances", 1)
local json = require("json")
mod.Total = 0
mod.Count = 0
local targetStage = LevelStage.STAGE1_1
local targetStageType = 4
local stageStr = '1c'
local targetTypes = {
    RoomType.ROOM_MINIBOSS,
    -- RoomType.ROOM_DICE,
    -- RoomType.ROOM_SACRIFICE
}

function RCClear()
    mod.Total = 0
    mod.Count = 0
    mod:Save()
end

function mod:Load()
    if not mod:HasData() then
        return
    end
    local data = json.decode(mod:LoadData())
    if data ~= nil then
        mod.Total = data.Total or 0
        mod.Count = data.Count or 0
    end
end
function mod:Save()
    local data = {
        Total = mod.Total,
        Count = mod.Count
    }
    mod:SaveData(json.encode(data))
end
mod:AddCallback(ModCallbacks.MC_POST_PLAYER_UPDATE, function(self)
    local level = Game():GetLevel()
    if level:GetStage() ~= targetStage or level:GetStageType() ~= targetStageType then
        Isaac.ExecuteCommand('stage ' .. stageStr)
    else
        self:Load()
        self.Total = self.Total + 1
        local rooms=level:GetRooms()
        local found = false
        for i=1,#rooms do
            local room = rooms:Get(i-1)
            local type = room.Data.Type
            for _,targetType in ipairs(targetTypes) do
                if type == targetType then
                    self.Count = self.Count + 1
                    found = true
                    break
                end
            end
            if found then
                break
            end
        end
        self:Save()
        Isaac.ExecuteCommand('restart')
    end
end)

mod:AddCallback(ModCallbacks.MC_POST_RENDER,function(self)
    local text = string.format('Target : Total = %d : %d = %.2f%%',self.Count,mod.Total,(mod.Count/mod.Total)*100)
    local textWidth = Isaac.GetTextWidth(text)
    Isaac.RenderText(text,Isaac.GetScreenWidth()/2 - textWidth/2,10,1,1,1,1)
end)