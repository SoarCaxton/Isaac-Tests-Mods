local CHESTS=RegisterMod('CHESTS',1)
Loop=3e3
Options.PauseOnFocusLost = false
CHESTS.Data={}
CHESTS.Total=0
CHESTS.LOCKED = false
CHESTS.PickupVariant2Name={}
local json = require('json')
for k,v in pairs(PickupVariant) do
    CHESTS.PickupVariant2Name[v]=k:match('^PICKUP_(.+)$')
end
function ChestsToggle()
    CHESTS.Data={}
    CHESTS.Total=0
    CHESTS.LOCKED = not CHESTS.LOCKED
    CHESTS:Save()
end
function CHESTS:Save()
    local saveData = {
        Data = self.Data,
        Total = self.Total,
        Locked = self.LOCKED
    }
    self:SaveData(json.encode(saveData))
end
function CHESTS:Load()
    if self:HasData() then
        local saveData = json.decode(self:LoadData())
        self.Data = saveData.Data or {}
        self.Total = saveData.Total or 0
        self.LOCKED = saveData.Locked or false
    end
end
function CHESTS:HashToPickupString(hash)
    local pickups = {}
    for k in string.gmatch(hash, '([^,]+)') do
        table.insert(pickups, tonumber(k))
    end
    local pickupString=''
    for k,v in ipairs(pickups) do
        pickupString=pickupString..self.PickupVariant2Name[v]..', '
    end
    pickupString=string.sub(pickupString,1,-3)
    return pickupString
end
CHESTS:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, function()
    local room = Game():GetRoom()
    for i=0,7 do
        room:RemoveDoor(i)
    end
end)

CHESTS:AddCallback(ModCallbacks.MC_POST_UPDATE, function(self)
    self:Load()
    local room = Game():GetRoom()
    for i=1,Loop do
        if self.LOCKED then
            Isaac.Spawn(EntityType.ENTITY_PICKUP,PickupVariant.PICKUP_LOCKEDCHEST,0,room:GetCenterPos(),Vector.Zero,nil)
        else
            Isaac.Spawn(EntityType.ENTITY_PICKUP,PickupVariant.PICKUP_LOCKEDCHEST,0,room:GetCenterPos(),Vector.Zero,nil)
        end
    end
    local entities = Isaac.GetRoomEntities()
    local pickups = {}
    for _,entity in pairs(entities) do
        if entity.Type == EntityType.ENTITY_PICKUP then
            table.insert(pickups,entity.Variant)
            entity:Remove()
        end
    end
    table.sort(pickups)
    if #pickups>0 then
        local shouldRestart=false
        for k,v in ipairs(pickups) do
            local hashkey=tostring(v)
            self.Data[hashkey] = self.Data[hashkey] and self.Data[hashkey] + 1 or 1
            self.Total = self.Total + 1
            if self.Total%1e4==0 then
                shouldRestart=true
            end
        end
        if shouldRestart then
            Isaac.ExecuteCommand('restart')
        end
    end
    self:Save()
end)

CHESTS:AddCallback(ModCallbacks.MC_POST_RENDER, function(self)
    local pos=Vector(Isaac.GetScreenWidth(),Isaac.GetScreenHeight())/4
    local tmp={}
    for k,v in pairs(self.Data) do
        table.insert(tmp,k)
    end
    table.sort(tmp)
    for _,k in pairs(tmp) do
        local v=self.Data[k]
        local pickupString=self:HashToPickupString(k)
        local percentage=(v/self.Total)*100
        local displayString=string.format('%s : %d (%.2f%%)',pickupString,v,percentage)
        Isaac.RenderScaledText(displayString,pos.X-Isaac.GetTextWidth(displayString)/4,pos.Y,.5,.5,1,1,1,1)
        pos.Y=pos.Y+10
    end
    local totalString = string.format('Total %s: %d',CHESTS.LOCKED and "Locked Chests" or "Chests", self.Total)
    Isaac.RenderScaledText(totalString,pos.X-Isaac.GetTextWidth(totalString)/4,pos.Y,.5,.5,0,1,0,1)
    local difficultyString = 'Difficulty: '..Game().Difficulty
    Isaac.RenderScaledText(difficultyString,pos.X-Isaac.GetTextWidth(difficultyString)/4,pos.Y+10,.5,.5,1,0,0,1)
end)

CHESTS:AddCallback(ModCallbacks.MC_PRE_MOD_UNLOAD, function(self)
    Options.PauseOnFocusLost = true
end)