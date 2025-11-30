local TR=RegisterMod('Tainted Rock',1)
Options.PauseOnFocusLost = false
TR.Data={}
TR.Total=0
TR.PickupVariant2Name={}
TR.SS=false
local json = require('json')
function TRToggle()
    TR.SS=not TR.SS
    TR.Data={}
    TR.Total=0
    TR:Save()
end
for k,v in pairs(PickupVariant) do
    TR.PickupVariant2Name[v]=k:match('^PICKUP_(.+)$')
end
function TR:Save()
    local saveData = {
        Data = self.Data,
        Total = self.Total,
        SS = self.SS
    }
    self:SaveData(json.encode(saveData))
end
function TR:Load()
    if self:HasData() then
        local saveData = json.decode(self:LoadData())
        self.Data = saveData.Data or {}
        self.Total = saveData.Total or 0
        self.SS = saveData.SS or false
    end
end
function TR:HashToPickupString(hash)
    local pickups = {}
    for k in string.gmatch(hash, '([^,]+)') do
        table.insert(pickups, tonumber(k))
    end
    local pickupString=''
    for k,v in ipairs(pickups) do
        pickupString=pickupString..TR.PickupVariant2Name[v]..', '
    end
    pickupString=string.sub(pickupString,1,-3)
    return pickupString
end
TR:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, function()
    local room = Game():GetRoom()
    for i=0,7 do
        room:RemoveDoor(i)
    end
end)

local StartingItems = require('tr_startingitems')
function TR:CheckStartingItems()
    local player = Isaac.GetPlayer(0)
    for _,item in pairs(StartingItems.Collectibles) do
        local itemId, num = table.unpack(type(item) == 'table' and item or {item, 1})
        while player:GetCollectibleNum(itemId) < num do
            player:AddCollectible(itemId, Isaac.GetItemConfig():GetCollectible(itemId).InitCharge)
        end
    end
    for _,item in pairs(StartingItems.Trinkets) do
        local itemId, num = table.unpack(type(item) == 'table' and item or {item, 1})
        while player:GetTrinketMultiplier(itemId) < num do
            player:DropTrinket(player.Position+player.PositionOffset)
            player:AddTrinket(itemId, true)
            player:UseActiveItem(CollectibleType.COLLECTIBLE_SMELTER, 3339)
        end
    end
end
TR:AddCallback(ModCallbacks.MC_POST_UPDATE, function(self)
    self:Load()
    local frame = Game():GetFrameCount()&1
    local room = Game():GetRoom()
    self:CheckStartingItems()
    if frame==0 then
        if self.SS then
            Isaac.GridSpawn(GridEntityType.GRID_ROCK_SS,0,room:GetCenterPos(),true)
        else
            Isaac.GridSpawn(GridEntityType.GRID_ROCKT,0,room:GetCenterPos(),true)
        end
        local entities = Isaac.GetRoomEntities()
        local pickups = {}
        for _,entity in pairs(entities) do
            if entity.Type == EntityType.ENTITY_PICKUP then
                table.insert(pickups,entity.Variant)
                entity:Remove()
            elseif entity.Type == EntityType.ENTITY_BOMB and (entity.Variant==BombVariant.BOMB_TROLL or entity.Variant==BombVariant.BOMB_SUPERTROLL or entity.Variant==BombVariant.BOMB_GOLDENTROLL) then
                table.insert(pickups,PickupVariant.PICKUP_BOMB)
                entity:Remove()
            end
        end
        table.sort(pickups)
        if #pickups>0 then
            local smallRockSpawned = false
            local hashkey=''
            for k,v in ipairs(pickups) do
                hashkey=hashkey..tostring(v)..','
                if v == PickupVariant.PICKUP_COLLECTIBLE then
                    smallRockSpawned = true
                end
            end
            hashkey=string.sub(hashkey,1,-2)
            self.Data[hashkey] = self.Data[hashkey] and self.Data[hashkey] + 1 or 1
            self.Total = self.Total + 1
            if smallRockSpawned then
                Isaac.ExecuteCommand('restart')
            end
        end
    else
        room:DestroyGrid(room:GetGridIndex(room:GetCenterPos()),true)
    end
    self:Save()
end)

TR:AddCallback(ModCallbacks.MC_POST_RENDER, function(self)
    local pos=Vector(Isaac.GetScreenWidth(),Isaac.GetScreenHeight())/4
    local tmp={}
    for k,v in pairs(self.Data) do
        table.insert(tmp,k)
    end
    table.sort(tmp)
    for _,k in pairs(tmp) do
        local v=self.Data[k]
        local pickupString=TR:HashToPickupString(k)
        local percentage=(v/self.Total)*100
        local displayString=string.format('%s : %d (%.2f%%)',pickupString,v,percentage)
        Isaac.RenderScaledText(displayString,pos.X-Isaac.GetTextWidth(displayString)/4,pos.Y,.5,.5,1,1,1,1)
        pos.Y=pos.Y+10
    end
    local totalString = string.format('Total %s: %d',self.SS and "SSRocks" or "TRocks", self.Total)
    Isaac.RenderScaledText(totalString,pos.X-Isaac.GetTextWidth(totalString)/4,pos.Y,.5,.5,0,1,0,1)
    local difficultyString = 'Difficulty: '..Game().Difficulty
    Isaac.RenderScaledText(difficultyString,pos.X-Isaac.GetTextWidth(difficultyString)/4,pos.Y+10,.5,.5,1,0,0,1)
end)

TR:AddCallback(ModCallbacks.MC_PRE_MOD_UNLOAD, function(self)
    Options.PauseOnFocusLost = true
end)